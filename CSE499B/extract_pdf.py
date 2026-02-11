import PyPDF2

def extract_text_from_pdf(pdf_path):
    try:
        with open(pdf_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return text
    except Exception as e:
        return f"Error: {e}"

# Extract from both PDFs
print("=" * 80)
print("PROJECT PROPOSAL 2:")
print("=" * 80)
proposal_text = extract_text_from_pdf("Project Proposal2.pdf")
print(proposal_text[:2000])  # Print first 2000 characters

print("\n\n" + "=" * 80)
print("UPDATED SYSTEM:")
print("=" * 80)
updated_text = extract_text_from_pdf("updated system.pdf")
print(updated_text[:2000])  # Print first 2000 characters
