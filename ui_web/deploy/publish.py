"""WSL-side static publisher. Invoked by deploy.ps1 with a base64 JSON argument."""
import base64
import fcntl
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from html.parser import HTMLParser


def log(stage, message):
    print(f'[{stage}] {message}', flush=True)


def inventory(directory):
    result = {}
    for base, dirs, files in os.walk(directory, followlinks=False):
        for name in dirs + files:
            path = Path(base) / name
            if path.is_symlink():
                raise ValueError(f'Symbolic links are not supported in deployment trees: {path}')
        for name in files:
            path = Path(base) / name
            if not path.is_file():
                raise ValueError(f'Unsupported file in deployment tree: {path}')
            digest = hashlib.sha256()
            with path.open('rb') as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                    digest.update(chunk)
            result[path.relative_to(directory).as_posix()] = digest.hexdigest()
    return result


def replace_contents(target, source):
    # Never replace target itself: Docker binds its directory inode.
    for child in target.iterdir():
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()
    for child in source.iterdir():
        dest = target / child.name
        if child.is_dir():
            shutil.copytree(child, dest)
        else:
            shutil.copy2(child, dest)


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'script' and attrs.get('src'):
            self.assets.append(attrs['src'])
        if tag == 'link' and attrs.get('href') and attrs.get('rel') in ('stylesheet', 'modulepreload'):
            self.assets.append(attrs['href'])


def verify(config, staged):
    base = config['base_url'].rstrip('/') + '/'
    expected = (staged / 'index.html').read_bytes()

    def get(url):
        with urllib.request.urlopen(url, timeout=15) as response:
            if response.status != 200:
                raise ValueError(f'HTTP {response.status}: {url}')
            return response.read()

    if get(base) != expected:
        raise ValueError('HTTP homepage differs from the staged index.html; check the gateway mount and URL.')
    get(urllib.parse.urljoin(base, config['health'].lstrip('/')))
    if get(urllib.parse.urljoin(base, '__deploy_spa_check__/nested')) != expected:
        raise ValueError('SPA fallback does not return the deployed index.html.')
    parser = AssetParser()
    parser.feed(expected.decode('utf-8'))
    if not parser.assets:
        raise ValueError('No script or stylesheet references found in index.html.')
    for asset in parser.assets:
        parsed = urllib.parse.urlsplit(asset)
        if parsed.scheme or parsed.netloc:
            raise ValueError('External asset references cannot be verified as local build files.')
        relative = urllib.parse.unquote(parsed.path).lstrip('/')
        file = (staged / relative).resolve()
        if not file.is_relative_to(staged.resolve()) or not file.is_file():
            raise ValueError(f'Asset does not resolve inside the build: {asset}')
        if get(urllib.parse.urljoin(base, asset)) != file.read_bytes():
            raise ValueError(f'HTTP asset differs from the build: {asset}')


def main(config):
    relative = PurePosixPath(config['site'])
    if (relative.is_absolute() or not relative.parts or any(p in ('.', '..') for p in config['site'].split('/'))
            or relative.parts[0] == '.web-deploy' or '\\' in config['site']):
        raise ValueError('SitePath must be a safe, nonempty relative Linux path.')
    root_text = config['root']
    if root_text == '~' or root_text.startswith('~/'):
        root_text = os.path.expanduser(root_text)
    if not os.path.isabs(root_text):
        raise ValueError('DeployRoot must be an absolute Linux path or begin with ~/.')
    root = Path(root_text).resolve(strict=True)
    if root == Path('/') or not root.is_dir():
        raise ValueError('DeployRoot must be an existing directory other than /.')
    target = root.joinpath(*relative.parts)
    current = root
    for part in relative.parts:
        current /= part
        if current.is_symlink():
            raise ValueError(f'Symbolic link in SitePath: {current}')
    if not target.resolve().is_relative_to(root) or target == root:
        raise ValueError('SitePath escapes DeployRoot.')
    metadata = root / '.web-deploy'
    if metadata.is_symlink():
        raise ValueError('Deployment metadata directory must not be a symbolic link.')
    metadata.mkdir(exist_ok=True)
    site_id = hashlib.sha256(str(relative).encode()).hexdigest()[:20]
    state = metadata / site_id
    if state.is_symlink():
        raise ValueError('Deployment state directory must not be a symbolic link.')
    state.mkdir(exist_ok=True)
    with (state / 'lock').open('a') as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError('Another deployment is active for this site.')
        publish_locked(config, target, state)


def publish_locked(config, target, state):
    output = Path(subprocess.check_output(['wslpath', '-a', '-u', config['output']], text=True).strip())
    if not (output / 'index.html').is_file():
        raise ValueError('Build output or index.html is unavailable in WSL.')
    if target.exists() and not target.is_dir():
        raise ValueError('SitePath exists but is not a directory.')
    if target.exists() and not config['overwrite']:
        raise ValueError('SitePath exists and AllowOverwrite is false.')
    before = inventory(target) if target.exists() else None
    source_inventory = inventory(output)
    work = Path(tempfile.mkdtemp(prefix='run-', dir=state))
    stage = work / 'stage'
    recovery = work / 'recovery'
    modified = False
    keep_work = False
    try:
        log('STAGING', 'Copying and verifying build files.')
        shutil.copytree(output, stage)
        if inventory(stage) != source_inventory:
            raise ValueError('Staging inventory differs from build output.')
        log('BACKUP', 'Preparing a recovery copy of the existing site.')
        if before is not None:
            shutil.copytree(target, recovery)
            if inventory(recovery) != before:
                raise ValueError('Recovery copy differs from the existing site.')
        target.mkdir(parents=True, exist_ok=True)
        modified = True
        log('PUBLISH', 'Updating the existing bind-mounted directory (non-atomic).')
        replace_contents(target, stage)
        if inventory(target) != source_inventory:
            raise ValueError('Published files differ from staging.')
        if config['verify']:
            log('VERIFY', 'Checking homepage, health, assets and SPA fallback.')
            verify(config, stage)
        else:
            log('VERIFY', 'HTTP checks disabled by configuration; published file hashes match.')
        if before is not None and config['backup']:
            backup = state / ('backup-' + work.name[4:])
            backup_staging = work / 'backup'
            shutil.copytree(recovery, backup_staging)
            backup_staging.rename(backup)
            log('BACKUP', f'Retained backup: {backup}')
            try:
                backups = sorted((p for p in state.glob('backup-*') if p.is_dir() and not p.is_symlink()), key=lambda p: p.stat().st_mtime_ns, reverse=True)
                for old in backups[config['retention']:]:
                    shutil.rmtree(old)
            except OSError as error:
                log('BACKUP', f'Warning: could not prune old backups: {error}')
    except Exception:
        if modified:
            try:
                log('PUBLISH', 'Failure detected; restoring the previous site.')
                if before is None:
                    for child in target.iterdir():
                        shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
                else:
                    replace_contents(target, recovery)
                    if inventory(target) != before:
                        raise ValueError('Restored files do not match the recovery copy.')
                log('PUBLISH', 'Previous site restored.')
            except Exception as restore_error:
                keep_work = True
                log('RESULT', f'Restore failed: {restore_error}. Recovery files retained at {work}')
        raise
    finally:
        if not keep_work:
            shutil.rmtree(work)


if __name__ == '__main__':
    try:
        main(json.loads(base64.b64decode(sys.argv[1]).decode('utf-8')))
    except Exception as error:
        log('RESULT', f'WSL publication failed: {error}')
        sys.exit(1)
