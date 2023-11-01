import glob
import os
from pathlib import Path

from pdf2image import convert_from_path
from rich.progress import track


class Slide2md:
    def __init__(self, course_folder: str):
        """Initialize"""
        self.course_folder = Path(course_folder)
        self.slides_folder = os.path.join(self.course_folder, "slides")
        self.docs_folder = os.path.join(self.course_folder, "docs")
        self.imgs_folder = os.path.join(self.docs_folder, "imgs")
        self.index_file = os.path.join(self.docs_folder, "README.md")

        for folder in [self.imgs_folder, self.slides_folder, self.docs_folder]:
            os.makedirs(folder, exist_ok=True)

        if not os.path.exists(self.index_file):
            with open(self.index_file, "w") as f:
                f.write("Course Index" + "\n" + "===" + "\n\n")
                f.close()

    def pdf2image(self, pdf_path, dpi: int = 100) -> None:
        """Convert PDF to images"""
        images = convert_from_path(pdf_path=pdf_path, dpi=dpi)
        pdf_name = os.path.basename(pdf_path).rsplit(".")[0]
        for i, image in track(enumerate(images), description=f"Converting {pdf_name}", total=len(images)):
            image_path = os.path.join(self.imgs_folder, pdf_name, f"{i+1:03}.png")
            image.save(fp=image_path)

    def create_md(self, pdf_name: str) -> None:
        """Create a markdown file for the given PDF"""
        image_directory = os.path.join(self.imgs_folder, pdf_name)
        images = sorted([file for file in os.listdir(image_directory)])
        markdown_images = [
            f"![{os.path.splitext(image)[0]}]({os.path.join('imgs', pdf_name, image)})\n" for image in images
        ]
        markdown_path = os.path.join(self.docs_folder, f"{pdf_name}.md")

        with open(markdown_path, "w") as f:
            f.write(pdf_name + "\n" + "===" + "\n\n")
            f.write("\n".join(markdown_images))
            f.close()

    def update_index_yaml(self):
        """Update the index.yaml file"""
        self.index_yaml = os.path.join(self.course_folder, "mkdocs.yaml")
        course_name = os.path.basename(self.course_folder)
        markdown_files = glob.glob(os.path.join(self.docs_folder, "*.md"))
        markdown_files = sorted([f for f in markdown_files if os.path.basename(f) != "README.md"])
        with open(self.index_yaml, "w") as f:
            f.write(f"site_name: {course_name}\n\n")
            f.write("nav:\n")
            f.write("   - Home: README.md\n")
            for markdown_file in markdown_files:
                markdown_name = os.path.basename(markdown_file).rsplit(".")[0]
                title_markdown_name = markdown_name.replace("-", " ").title()
                f.write(f"   - {title_markdown_name}: {markdown_name}.md\n")
            f.close()

    def run(self):
        """Run the slide2md script."""
        # Find the PDFs not yet converted
        pdfs_not_converted = []
        for pdf in os.listdir(self.slides_folder):
            pdf_path = os.path.join(self.slides_folder, pdf)
            pdf_name = os.path.basename(pdf_path).rsplit(".")[0]
            img_folder = os.path.join(self.imgs_folder, pdf_name)

            if os.path.exists(img_folder):
                continue
            else:
                pdfs_not_converted.append(pdf)

        # Convert the PDFs
        if pdfs_not_converted == []:
            print("All slides converted!")

        else:
            for pdf in sorted(pdfs_not_converted):
                pdf_path = os.path.join(self.slides_folder, pdf)
                pdf_name = os.path.basename(pdf_path).rsplit(".")[0]
                img_folder = os.path.join(self.imgs_folder, pdf_name)
                os.makedirs(name=img_folder)
                self.pdf2image(pdf_path=pdf_path)
                self.create_md(pdf_name=pdf_name)

            self.update_index_yaml()
            print("Done!")
