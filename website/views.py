from flask import Blueprint,flash,redirect, render_template,request,url_for,session
from flask_login import  login_required,current_user
from werkzeug.utils import secure_filename
from flask_paginate import Pagination, get_page_args
import os
from .utils import *
model = pickle.load(open('website/model.pkl', 'rb'))
cv = pickle.load(open('website/cv.pkl', 'rb'))
dic=[]
views = Blueprint('views', __name__)
def get_dic(offset=0, per_page=3,dic=[]):
    return dic[offset: offset + per_page]

@views.route('/', methods=['GET','POST'])
@login_required
def home():
    if request.method == 'POST':

        if not 'file' in request.files:
            flash('No file part in request',category='error')
            return redirect(request.url)
        file = request.files.get('file')
        if file.filename=='':
            flash('No file uploaded',category='error')
        elif file_valid(file.filename):
            filename=file.filename
            listword= predict(file, filename, cv, model)
            global dic;
            dic =define_keywords(listword)
            return redirect(url_for('views.result'))
        else:
            flash('file no valid!!', category='error')
    return render_template("home.html", user=current_user)

@views.route('/result')
@login_required
def result():
    global dic;
    page, per_page, offset = get_page_args(page_parameter='page', per_page_parameter='per_page')
    total = len(dic)
    pagination_dic = get_dic(offset=offset, per_page=per_page, dic=dic)
    pagination = Pagination(page=page, per_page=per_page, total=total, css_framework='bootstrap4')
    return render_template('result.html', user=current_user, dic=pagination_dic, page=page, per_page=per_page, pagination=pagination)
