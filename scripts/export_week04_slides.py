"""Render selected instructor-supplied PDF pages without editing their content."""
import argparse
import hashlib
import json
from pathlib import Path
import pypdfium2 as pdfium

PAGES = [2, 3, 4, 6, 8, 9, 14, 15, 17, 18, 22, 23, 24, 25, 26, 27,
         28, 29, 31, 33, 34, 35, 36, 38, 39]


def export(source, destination):
    destination.mkdir(parents=True, exist_ok=True)
    document = pdfium.PdfDocument(source)
    files = {}
    for number in PAGES:
        page = document[number - 1]
        width, height = page.get_size()
        bitmap = page.render(scale=1400 / width)
        image = bitmap.to_pil()
        path = destination / f'slide-{number:02d}.png'
        image.save(path)
        files[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        image.close(); bitmap.close(); page.close()
    document.close()
    record = {'source': source.name, 'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'source_pages': 40, 'pages': PAGES, 'files': files,
              'note': 'Original lecture pages, not edited images. The older name M12 refers to the same synthetic classroom case now named CONV-3. Lesson text explains the API, workflow, MiniGPT and simplified-code corrections where relevant.'}
    (destination / 'SOURCE.json').write_text(json.dumps(record, indent=2) + '\n', encoding='utf-8', newline='\n')
    (destination / 'README.md').write_text('# Week 4 lecture pages\n\nThese are selected pages rendered from the instructor-supplied 40-page lecture PDF. Use each image with the saved lesson explanation. The lesson explains the picture before connecting it to source code. Original labels and illustrative code are preserved; use the current CONV-3 code for execution.\n', encoding='utf-8', newline='\n')
    print(f'Rendered {len(files)} original pages.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('--out', type=Path, default=Path(__file__).resolve().parents[1] / 'week04/slides')
    args = parser.parse_args()
    export(args.source, args.out)
