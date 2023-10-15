import numpy as np
from flask import Flask, request, jsonify, render_template
import pickle
import re
import os
import pandas as pd
import PyPDF2
import textract
import platform
from tempfile import TemporaryDirectory
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import aspose.words as aw

import wikipedia
import datetime
def Reading_Text(doc,PDF_file):
    PDF_file='website/static/files/'+PDF_file
    if PDF_file.rsplit('.', 1)[1].lower() in ['doc','docx']:
            doc.save(os.path.join(PDF_file))
            file_path=PDF_file
            for i in range(len(file_path)):
                if file_path[len(file_path) - i - 1] == '.':
                    extension = file_path[len(file_path) - i: len(file_path)]
                    PDF_file = file_path[0: len(file_path) - i] + 'pdf'
                    break;
            # Load word document
            doc = aw.Document(file_path)


    doc.save(os.path.join(PDF_file))

    # Store all the pages of the PDF in a variable
    image_file_list = []
    # Main execution point of the program'''
    with TemporaryDirectory() as tempdir:

        # Part 1 : Converting PDF to images

        if platform.system() == "Windows":
            pdf_pages = convert_from_path(PDF_file)
        else:
            pdf_pages = convert_from_path(PDF_file, 500)
            # Read in the PDF file at 500 DPI

        # Iterate through all the pages stored above
        for page_enumeration, page in enumerate(pdf_pages, start=1):
            # enumerate() "counts" the pages for us.

            # Create a file name to store the image
            filename = f"{tempdir}\page_{page_enumeration:03}.jpg"

            # Save the image of the page in system
            page.save(filename, "JPEG")
            image_file_list.append(filename)

        # Part 2 - Recognizing text from the images using OCR

        # Iterate from 1 to total number of pages
        text_output = ''
        for image_file in image_file_list:
            # Recognize the text as string in image using pytesserct
            text = str(((pytesseract.image_to_string(Image.open(image_file)))))

            text = text.replace("-\n", "")
            text_output += text
        return text_output
def weightage(word,text,number_of_documents=1):
    word_list = re.findall(word,text)
    number_of_times_word_appeared =len(word_list)
    tf = number_of_times_word_appeared/float(len(text))
    idf = np.log((number_of_documents)/float(number_of_times_word_appeared))
    tf_idf = tf*idf
    return number_of_times_word_appeared,tf,idf ,tf_idf

def Extracting_Keywords(text):
    ListLigne = text.split("\n")

    ListLigne = list(filter((' ').__ne__, ListLigne))

    taile = len(ListLigne)

    pattern = r"[a-zA-Z]\w+"

    keywords = []

    for i in range(taile):
        keywordLigne = re.findall(pattern, ListLigne[i].lower())
        keywords += keywordLigne
    keywords = list(dict.fromkeys(keywords))
    df = pd.DataFrame(list(set(keywords)),columns=['keywords'])  # Dataframe with unique keywords to avoid repetition in rows
    text = text.lower()  # Lowercasing each word

    df['number_of_times_word_appeared'] = df['keywords'].apply(lambda x: weightage(x, text)[0])
    df['tf'] = df['keywords'].apply(lambda x: weightage(x, text)[1])
    df['idf'] = df['keywords'].apply(lambda x: weightage(x, text)[2])
    df['tf_idf'] = df['keywords'].apply(lambda x: weightage(x, text)[3])
    best_keywords = df.loc[(df.number_of_times_word_appeared <= 20)]
    products_list = best_keywords.keywords.values.tolist()

    return products_list

def computer_words(model, words, cv):
    X = {'keywords': [words]}
    X = pd.DataFrame(data=X)
    X = X['keywords']
    Xcv = cv.transform(X)

    proba = list(zip(model.classes_, model.predict_proba(Xcv)[0]))
    preds = model.predict(Xcv)

    if preds[0] == 1:
            return True

    return False

def predict(file,filename,cv,model):
    '''
    For rendering results on HTML GUI
    '''
    text = Reading_Text(file,filename)
    products_list = Extracting_Keywords( text = text)
    products_list.sort()
    computer_words_list = []

    for item in products_list:
        if computer_words(model, item, cv):
            computer_words_list.append(item)

    return computer_words_list


def define_keywords(computer_words_list):
    listword = []
    for words in computer_words_list:
        l=[]
        wikipedia.set_lang("fr")


        try:

            l.append(wikipedia.summary(words + '(informatique)', sentences=2))
            l.append(wikipedia.page(words + '(informatique)').url)
            l.append(words)

        except Exception:
            wikipedia.set_lang("en")
            try:

                l.append(wikipedia.summary(words + '(computer science)', sentences=2))
                l.append(wikipedia.page(words + '(computer science)').url)
                l.append(words)
            except Exception:
                pass
        if len(l)==3:
            listword.append(l)
    return listword

ALLOWED_EXTENSIONS = {'pdf','doc','docx'}
def file_valid(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS