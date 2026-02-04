from datetime import datetime
from sqlalchemy import select, or_
from models import User,Palet,SessionLocal
from flask import Flask, json, request, jsonify, render_template, redirect, url_for, make_response,g,session, send_file,flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from typing import Any, Dict, List, Optional
import os
import dotenv
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

#------------------------------- Login -------------------------------#
@app.route("/login",methods=["GET","POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    if request.method=="GET":
        return render_template("login.html")
    email=(request.form.get("email")or"").strip().lower()
    password=request.form.get("password")or""
    if not email or password:
        flash("email a heslo sú povinne")
        return redirect(url_for("login"))
