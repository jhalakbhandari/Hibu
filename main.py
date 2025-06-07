from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import List
import pandas as pd
import os, smtplib, random
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

app = FastAPI()

# Allow frontend requests (adjust origins in production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change in production
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
TEMPLATE_DIR = "templates"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/send-emails/")
async def send_emails(
    file: UploadFile,
    resume: UploadFile,
    templates: List[str] = Form(...),
    sender_email: str = Form(...),
    sender_password: str = Form(...)
):
    csv_path = os.path.join(UPLOAD_DIR, file.filename)
    resume_path = os.path.join(UPLOAD_DIR, resume.filename)

    # Save files
    with open(csv_path, "wb") as f:
        f.write(await file.read())

    with open(resume_path, "wb") as f:
        f.write(await resume.read())

    df = pd.read_csv(csv_path)

    # Send email logic
    for _, row in df.iterrows():
        template_name = random.choice(templates)
        template_path = os.path.join(TEMPLATE_DIR, template_name)
        with open(template_path, "r", encoding="utf-8") as f:
            body = f.read().format(
                name=row['Name'],
                position=row['Position'],
                company=row['Company']
            )

        msg = MIMEMultipart()
        msg["From"] = sender_email
        msg["To"] = row["Email"]
        msg["Subject"] = f"Application for {row['Position']} at {row['Company']}"
        msg.attach(MIMEText(body, "plain"))

        with open(resume_path, "rb") as f:
            part = MIMEApplication(f.read(), Name=resume.filename)
        part['Content-Disposition'] = f'attachment; filename="{resume.filename}"'
        msg.attach(part)

        try:
            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(msg["From"], msg["To"], msg.as_string())
            server.quit()
        except Exception as e:
            return JSONResponse(status_code=500, content={"error": str(e)})

    return {"status": "Emails sent successfully"}
