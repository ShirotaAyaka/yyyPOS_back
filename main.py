from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, CHAR, func
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from pydantic import BaseModel
import mysql.connector
import os
from dotenv import load_dotenv

app = FastAPI() #ベース。空箱を作る

# .envファイルの内容をロード
load_dotenv()

# CORS設定 (NEXT.jsからのリクエストを許可する)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

config = {
  'host': os.getenv('DB_HOST'),
  'user': os.getenv('DB_USER'),
  'password': os.getenv('DB_PASSWORD'),
  'database': os.getenv('DB_NAME'),
  'client_flags': [mysql.connector.ClientFlag.SSL],
  'ssl_ca': '/home/site/certificates/DigiCertGlobalRootG2.crt.pem'
}
# SQLAlchemy接続URLの構築
DATABASE_URL = (
    f"mysql+mysqlconnector://{config['user']}:{config['password']}@{config['host']}/{config['database']}?"
    f"ssl_ca={config['ssl_ca']}"
)

# データベースの設定 (MySQLとの接続)
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# データベースセッションの依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# モデルの定義 (例として商品モデル)
class ItemModel(Base):
    __tablename__ = "商品マスタ"
    prd_id = Column(Integer, primary_key=True)
    code = Column(CHAR(13), unique=True, nullable=False)
    name = Column(String(50), nullable=False)
    price = Column(Integer, nullable=False)

# Pydanticモデル
class CodeRequest(BaseModel):
    code: str

@app.get("/")
def home():
    return {"message": "FastAPIで作成"}

@app.get("/check")
async def check():
    return {"message": "確認しました"}

# 商品のリストを取得するエンドポイント
@app.get("/items/")
def get_all_items(db: Session = Depends(get_db)):
    # 商品マスタテーブルから全てのデータを取得
    items = db.query(ItemModel).all()
    # デバッグ用に取得したデータを表示
    print("デバッグ: 全商品リスト -", items)
    # 取得したデータをリスト形式で返す
    return [{"prd_id": item.prd_id, "code": item.code, "name": item.name, "price": item.price} for item in items]