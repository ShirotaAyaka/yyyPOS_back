from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

app = FastAPI() #ベース。空箱を作る

# .envファイルの内容をロード
load_dotenv()

# CORS設定 (NEXT.jsからのリクエストを許可する)
origins = [
    "http://localhost:3000",
    "tech0-gen-7-step4-studentwebapp-pos-31-bzeyaydshdh9escq.eastus-01.azurewebsites.net",  # NEXT.jsのデフォルトポート
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "FastAPIで作成"}

@app.get("/check")
async def check():
    return {"message": "確認しました"}