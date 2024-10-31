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


# 取引マスタモデル
class TransactionModel(Base):
    __tablename__ = "取引マスタ"
    TRD_ID = Column(Integer, primary_key=True, autoincrement=True)
    EMP_CD = Column(CHAR(10), nullable=False)
    STORE_CD = Column(CHAR(5), nullable=False) 
    POS_NO = Column(CHAR(3), nullable=False)
    TOTAL_AMT = Column(Integer, nullable=False)

# Pydanticモデルにstore_cdを追加
class PurchaseRequest(BaseModel):
    items: list
    emp_cd: str
    store_cd: str  # store_cdを追加
    pos_no: str
    total_amt: int

# 取引明細モデル
class TransactionDetailModel(Base):
    __tablename__ = "取引明細"
    TRD_ID = Column(Integer, primary_key=True)
    DTL_ID = Column(Integer, primary_key=True)
    PRD_ID = Column(Integer, nullable=False)
    PRD_CODE = Column(CHAR(13), nullable=False)
    PRD_NAME = Column(String(50), nullable=False)
    PRD_PRICE = Column(Integer, nullable=False)



# 商品を取得するエンドポイント
@app.post("/items/")
def get_item_by_code(request: CodeRequest, db: Session = Depends(get_db)):
    item = db.query(ItemModel).filter(ItemModel.code == request.code).first()
    print("デバッグ: クエリ結果 -", item) 
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"prd_id": item.prd_id, "name": item.name, "price": item.price}

# 購入リクエストを処理するエンドポイント
@app.post("/purchase")
def process_purchase(request: PurchaseRequest, db: Session = Depends(get_db)):
    # 合計金額を計算
    total_amount = sum(item['price'] for item in request.items)

    transaction = TransactionModel(
        EMP_CD=request.emp_cd,
        STORE_CD=request.store_cd,  # STORE_CDを追加
        POS_NO=request.pos_no,
        TOTAL_AMT=total_amount,
    )
    db.add(transaction)
    db.commit()

    # 生成されたTRD_IDを取得
    trd_id = transaction.TRD_ID

    # 取引明細に購入リストを追加
    for index, item in enumerate(request.items):
        detail = TransactionDetailModel(
            TRD_ID=trd_id,
            DTL_ID=index + 1,  # 各商品の枝番を生成
            PRD_ID=item['prd_id'],
            PRD_CODE=item['code'],
            PRD_NAME=item['name'],
            PRD_PRICE=item['price'],
        )
        db.add(detail)

    # すべての取引明細をデータベースに保存
    db.commit()

    return {
        "message": "Purchase processed successfully", 
        "transaction_id": trd_id,
        "total_amt": total_amount
        }

Base.metadata.create_all(bind=engine)


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