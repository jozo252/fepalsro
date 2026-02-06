from datetime import datetime
from sqlalchemy import select, or_
from models import User,Palet,SessionLocal, Stock, StockMove
from flask import Flask, json, request, jsonify, render_template, redirect, url_for, make_response,g,session, send_file,flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from typing import Any, Dict, List, Optional
import os
import dotenv
from sqlalchemy.exc import IntegrityError
from urllib.parse import urlparse, urljoin
dotenv.load_dotenv()
app=Flask(__name__)
app.secret_key="supersecretkey"
login_manager=LoginManager()
login_manager.login_view="login"
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
    s=SessionLocal()
    try:
        return s.get(User,int(user_id))
    finally:
        s.close()

#------------------------------ ROUTES ---------------------------------#
@app.route("/")
@login_required
def home():
    return render_template("home.html")

@app.route("/palet/create", methods=["POST","GET"])
@login_required
def create_palet():
    db=SessionLocal()
    try:
        if request.method== "GET":
            palets=db.query(Palet).filter(Palet.user_id == current_user.id).all()
            if not palets:
                flash("Nemáš ešte záznamy v paletach")
                return render_template("create_palet.html")
            return render_template("create_palet.html", palets=palets)
        name=(request.form.get("name")or"").strip()
        sizes=(request.form.get("sizes")or"").strip() 
        if not name:
            flash("Názov je povinný")
            return redirect(url_for("create_palet"))
        exists = (
            db.query(Palet.id)
            .filter(
                Palet.user_id == current_user.id,
                Palet.name == name
            )
            .first()
            is not None
        )
        if exists:
            flash("Názov palety, uź existuje")
            return redirect(url_for("create_palet"))
        palet= Palet(
            name=name,
            sizes=sizes,
            user_id=current_user.id
        )
        db.add(palet)
        db.commit()
        return redirect(url_for("create_palet"))
    finally:
        db.close()

@app.route("/palet/<int:palet_id>/delete", methods=["POST"])
@login_required
def delete_palet(palet_id):
    db=SessionLocal()
    try:
        palet=db.query(Palet).filter(Palet.user_id == current_user.id, Palet.id == palet_id ).first()
        if not palet:
            flash("Nenašiel sa typ palety")
            return redirect(url_for("create_palet"))
        db.delete(palet)
        db.commit()
        flash("Úspešne vymazane")
        return redirect(url_for("create_palet"))
    finally:
        db.close()

@app.route("/warehouse", methods=["GET","POST"])
@login_required
def warehouse():
    db=SessionLocal()
    try:
        if request.method=="GET":
            q = request.args.get("q","").strip()
            from_ = request.args.get("from","").strip()
            to_ = request.args.get("to","").strip()
            palets=db.query(Palet).filter(Palet.user_id == current_user.id).all()
            stocks=db.query(Stock).filter(Stock.user_id == current_user.id).all()
            

            moves_q = (
                db.query(StockMove, Palet)
                .join(Palet, Palet.id == StockMove.palet_id)
                .filter(StockMove.user_id == current_user.id)
            )

            if q:
                like = f"%{q}%"
                moves_q = moves_q.filter(or_(Palet.name.ilike(like), StockMove.note.ilike(like)))

            if from_:
                from_dt = datetime.strptime(from_, "%Y-%m-%d")
                moves_q = moves_q.filter(StockMove.created_at >= from_dt)

            if to_:
                to_dt = datetime.strptime(to_, "%Y-%m-%d") + timedelta(days=1)
                moves_q = moves_q.filter(StockMove.created_at < to_dt)

            moves = moves_q.order_by(StockMove.created_at.desc()).limit(50).all()
            stock_map={s.palet_id: s.qty for s in stocks}
            return render_template("warehouse.html", palets=palets, stock_map=stock_map, moves=moves)

        palet_id=int(request.form.get("palet_id"))
        amount=int(request.form.get("amount"))
        action=(request.form.get("action") or "").strip() 
        note=(request.form.get("note") or "").strip()
        if amount <= 0:
            flash("Množstvo musí byť väčšie ako 0")
            return redirect(url_for("warehouse")) 
        if action == "add":
            delta = amount
        elif action == "remove":
            delta = -amount
        else:
            flash("neplatna akcia")
            return redirect(url_for("warehouse"))
        palet=db.query(Palet).filter(
            Palet.id==palet_id,
            Palet.user_id==current_user.id
        ).first()    
        if not palet:
            flash("Neplatny typ palety")
            return redirect(url_for("warehouse"))
        stock=db.query(Stock).filter(
            Stock.user_id==current_user.id,
            Stock.palet_id==palet_id
        ).first()
        if not stock:
            stock = Stock(
                user_id=current_user.id, palet_id = palet_id,qty=0
            )
            db.add(stock)
        if stock.qty+delta <0:
            flash("nedostatok na sklade")
            return redirect(url_for("warehouse"))
        stock.qty += delta
        db.add(StockMove(
            user_id=current_user.id, palet_id=palet_id, delta=delta, note=note
        ))
        db.commit()
        return redirect(url_for("warehouse"))
    finally:
        db.close()

#------------------------------ END of ROUTES ---------------------------------#
#------------------------------- Login -------------------------------#
def is_safe_url(target):
    # aby ti niekto nedal next=https://evil.com
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("login.html")

    email = (request.form.get("email") or "").strip().lower()
    password = (request.form.get("password") or "").strip()

    if not email or not password:
        flash("Email a heslo sú povinné.", "danger")
        return redirect(url_for("login"))

    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user is None or not user.check_password(password):
            flash("Nesprávny email alebo heslo.", "danger")
            return redirect(url_for("login"))

        login_user(user, remember=True)  # remember=False ak nechceš cookie “zapamätať”
        flash("Prihlásenie úspešné.", "success")

        next_url = request.args.get("next")
        if next_url and is_safe_url(next_url):
            return redirect(next_url)

        return redirect(url_for("home"))

    finally:
        db.close()

@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("register.html")

    db = SessionLocal()
    try:
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = (request.form.get("password") or "").strip()
        password2 = (request.form.get("password2") or "").strip()

        if not username or not email or not password or not password2:
            flash("Všetky polia sú povinné.", "danger")
            return redirect(url_for("register"))

        if password != password2:
            flash("Heslá sa nezhodujú.", "danger")
            return redirect(url_for("register"))

        existing = db.query(User).filter(User.email == email).first()
        if existing:
            flash("Používateľ s týmto emailom už existuje.", "warning")
            return redirect(url_for("register"))

        user = User(username=username, email=email)
        user.set_password(password)

        db.add(user)
        db.commit()

        flash("Registrácia úspešná.", "success")
        return redirect(url_for("home"))

    except IntegrityError:
        db.rollback()
        flash("Účet už existuje (duplicitný email/username).", "warning")
        return redirect(url_for("register"))
    except Exception as e:
        db.rollback()
        flash("Chyba pri registrácii.", "danger")
        return redirect(url_for("register"))
    finally:
        db.close()
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("Odhlásený.", "info")
    return redirect(url_for("login"))
#------------------------------- END of Login -------------------------------#


if __name__ == "__main__":
    app.run(debug=True)

    
