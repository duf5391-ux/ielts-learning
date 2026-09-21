"""Copy the fully validated portable build into the isolated Pages repository."""
from pathlib import Path
import importlib.util
import json
import shutil
import uuid

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'web-publication'
TARGET = ROOT / 'github-publication'


def remove_stage(path):
    resolved = path.resolve()
    allowed = (TARGET / '.staging').resolve()
    if resolved == allowed or not resolved.is_relative_to(allowed):
        raise ValueError('Refusing cleanup outside isolated staging: ' + str(resolved))
    if resolved.exists():
        shutil.rmtree(resolved)


def main():
    spec = importlib.util.spec_from_file_location('pages_validate', TARGET / 'validate.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source_manifest_bytes = (SOURCE / 'publication-manifest.json').read_bytes()
    source_manifest = json.loads(source_manifest_bytes)
    module.validate(SOURCE / 'dist', source_manifest)
    # Publish fingerprints only: omit local source paths and hosting credentials/IDs.
    fields = ('source_html_sha256', 'published_html_sha256', 'save_fields',
              'published_files', 'total_bytes', 'html_pages_checked',
              'scripts_syntax_checked', 'dictionary', 'files')
    manifest = {key: source_manifest[key] for key in fields}
    stage = TARGET / '.staging' / uuid.uuid4().hex
    stage.mkdir(parents=True)
    staged_site = stage / 'site'
    old_site = stage / 'previous-site'
    site = TARGET / 'site'
    old_manifest = (TARGET / 'manifest.json').read_bytes() if (TARGET / 'manifest.json').exists() else None
    installed = False
    backed_up = False
    cleanup = False
    try:
        if old_manifest is not None:
            (stage / 'previous-manifest.json').write_bytes(old_manifest)
        shutil.copytree(SOURCE / 'dist', staged_site)
        module.validate(staged_site, manifest)
        if (SOURCE / 'publication-manifest.json').read_bytes() != source_manifest_bytes:
            raise ValueError('Publication build changed while staging; rebuild and retry')
        # Both validations must complete before replacing the prior site.
        if site.exists():
            site.rename(old_site)
            backed_up = True
        staged_site.rename(site)
        installed = True
        new_manifest = stage / 'manifest.json'
        new_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        new_manifest.replace(TARGET / 'manifest.json')
        result = module.validate(site, manifest)
        cleanup = True
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        try:
            if installed and site.exists():
                site.rename(stage / 'failed-site')
            if backed_up:
                old_site.rename(site)
            if old_manifest is not None:
                (TARGET / 'manifest.json').write_bytes(old_manifest)
            elif (TARGET / 'manifest.json').exists():
                (TARGET / 'manifest.json').unlink()
            cleanup = True
        except Exception as recovery_error:
            raise RuntimeError('Rollback interrupted; preserved recovery files at ' + str(stage)) from recovery_error
        raise
    finally:
        if cleanup:
            remove_stage(stage)


if __name__ == '__main__':
    main()
