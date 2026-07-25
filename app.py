import os
import sys
import tempfile
import uuid
import logging
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, send_file

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from redact import redact_document
from utils import setup_logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", os.urandom(24).hex())
app.config["MAX_CONTENT_LENGTH"] = 20 * 1024 * 1024

ALLOWED_EXTENSIONS = {"docx"}
PROJECT_ROOT = Path(__file__).resolve().parent
MAPPING_PATH = str(PROJECT_ROOT / "mapping.json")


logger = logging.getLogger(__name__)
setup_logging("INFO")


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/redact", methods=["POST"])
def redact():
    if "file" not in request.files:
        flash("No file part in the request.", "error")
        return redirect(url_for("index"))

    file = request.files["file"]

    if file.filename == "":
        flash("No file selected.", "error")
        return redirect(url_for("index"))

    if not allowed_file(file.filename):
        flash("Invalid file type. Only .docx files are allowed.", "error")
        return redirect(url_for("index"))

    try:
        unique_id = uuid.uuid4().hex[:12]
        temp_input = tempfile.NamedTemporaryFile(
            suffix=".docx", delete=False, dir=str(PROJECT_ROOT / "input")
        )
        file.save(temp_input.name)
        temp_input.close()

        output_name = f"redacted_{unique_id}.docx"
        temp_output = str(PROJECT_ROOT / "output" / output_name)

        redact_document(temp_input.name, temp_output, MAPPING_PATH)

        os.unlink(temp_input.name)

        return render_template(
            "index.html",
            success=True,
            download_path=url_for("download", filename=output_name),
            filename=file.filename,
        )
    except Exception as e:
        logger.exception("Error during redaction: %s", str(e))
        flash(f"An error occurred during processing: {str(e)}", "error")
        return redirect(url_for("index"))


@app.route("/download/<filename>")
def download(filename: str):
    file_path = str(PROJECT_ROOT / "output" / filename)
    if not os.path.isfile(file_path):
        flash("File not found.", "error")
        return redirect(url_for("index"))
    return send_file(
        file_path,
        as_attachment=True,
        download_name="redacted_" + filename.replace("redacted_", ""),
    )


if __name__ == "__main__":
    os.makedirs(str(PROJECT_ROOT / "input"), exist_ok=True)
    os.makedirs(str(PROJECT_ROOT / "output"), exist_ok=True)
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)