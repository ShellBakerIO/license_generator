from fastapi import FastAPI

app = FastAPI()

@app.post("/generate_license")
def generate_license(current_user: Annotated[Session, Depends(get_current_user)],
                     lic: LicensesInfo = Depends(LicensesInfo.as_form),
                     machine_digest_file: UploadFile = File(...),
                     db: Session = Depends(get_db)):
  pass

@app.get("/all_licenses")
def get_all_licenses(current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
  pass

@app.get("/license/{id}")
def find_license(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
  pass

@app.get("/machine_digest_file/{id}")
def find_machine_digest(id: int, current_user: Annotated[Session, Depends(get_current_user)], db: Session = Depends(get_db)):
  pass