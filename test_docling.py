import time
from pathlib import Path
from documents.docling_pipeline import extract_markdown

pdf_folder = Path("test_pdfs")

for pdf_path in pdf_folder.glob("*.pdf"):
    print(f"\n\n===== {pdf_path.name} =====")

    start = time.time()

    output = extract_markdown(pdf_path)

    end = time.time()

    print(f"Time taken: {end - start:.2f} seconds")
    print(output[:300])