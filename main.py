# ---------------- Core Libraries ----------------
import os
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import joblib

# ---------------- Visualization ----------------
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------- Scikit-learn ----------------
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix
)
from sklearn.ensemble import GradientBoostingClassifier

# ---------------- Advanced Models ----------------
from lightgbm import LGBMClassifier
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV

# ---------------- Sparse Matrix ----------------
from scipy.sparse import hstack

# ---------------- Database ----------------
from pymongo import MongoClient 

# ---------------- GUI (Tkinter) ----------------
import tkinter
import tkinter as tk
from tkinter import (
    messagebox,
    filedialog,
    Text,
    END,
    Label,
    Scrollbar,
    ttk
)

# ---------------- Images ----------------
from PIL import Image, ImageTk


main = tkinter.Tk()
main.configure(bg='#f0f8ff')  # Light background
main.title("Multi-modal Product Recommendation System using Pricing, Brand, and Description Feature Fusion") 
screen_width = main.winfo_screenwidth()
screen_height = main.winfo_screenheight()

# Set window size to full screen
main.geometry(f"{screen_width}x{screen_height}")

global dataset, X, y
global X_train, X_test, y_train, y_test

MODEL_DIR = "models"
RESULTS_DIR = "results"
os.makedirs(MODEL_DIR, exist_ok=True)
os.makedirs(RESULTS_DIR, exist_ok=True)

def uploadDataset():
    global filename
    global dataset
    filename = filedialog.askopenfilename(initialdir = "Dataset")
    text.delete('1.0', END)
    text.insert(END,filename+' Loaded\n')
    dataset = pd.read_csv(filename)
    text.insert(END,str(dataset)+"\n\n")


def preprocess_data(df, is_train=True):
    text.delete('1.0', END)
    global X, y
    df = df.copy()

    # ---------------- Text Cleanup ----------------
    df["content"] = (
        df.get("name", "") + " " +
        df.get("description.short", "") + " " +
        df.get("description.complete", "")
    ).astype(str).str.lower()

    # ---------------- Brand Encoding ----------------
    brand_enc_path = os.path.join(MODEL_DIR, "brand_encoder.pkl")
    if is_train:
        brand_le = LabelEncoder()
        df["brand_encoded"] = brand_le.fit_transform(df["brandName"])
        joblib.dump(brand_le, brand_enc_path)
    else:
        brand_le = joblib.load(brand_enc_path)
        df["brand_encoded"] = brand_le.transform(df["brandName"])

    # ---------------- Target Encoding ----------------
    target_enc_path = os.path.join(MODEL_DIR, "product_type_encoder.pkl")
    if "product_type" in df.columns:
        if is_train:
            target_le = LabelEncoder()
            y = target_le.fit_transform(df["product_type"])
            joblib.dump(target_le, target_enc_path)
        else:
            target_le = joblib.load(target_enc_path)
            y = target_le.transform(df["product_type"])
    else:
        y = None  # No labels in this dataset

    # ---------------- Text Vectorization ----------------
    vectorizer = HashingVectorizer(
        n_features=2**18,
        stop_words="english",
        ngram_range=(1, 2),
        alternate_sign=False
    )
    X_text = vectorizer.transform(df["content"])

    # ---------------- Categorical Feature Scaling ----------------
    scaler_path = os.path.join(MODEL_DIR, "cat_scaler.pkl")
    cat_features = df[["brand_encoded"]]

    if is_train:
        scaler = StandardScaler(with_mean=False)
        X_cat = scaler.fit_transform(cat_features)
        joblib.dump(scaler, scaler_path)
    else:
        scaler = joblib.load(scaler_path)
        X_cat = scaler.transform(cat_features)

    # ---------------- Combine Features ----------------
    X = hstack([X_text, X_cat])
    text.insert(END, f"Preprocessing completed:")
    text.insert(END, f"{X} {y}")

    return X, y

def perform_eda(df):
    global dataset

    plt.figure()
    plt.scatter(
        df["pricing.retailPrice.value"],
        df["pricing.finalPrice.value"],
        alpha=0.3
    )
    plt.xlabel("Retail Price")
    plt.ylabel("Final Price")
    plt.title("Retail Price vs Final Price")
    plt.show()

    plt.figure()
    df["brandName"].value_counts().head(10).plot(kind="bar")
    plt.xlabel("Brand")
    plt.ylabel("Number of Products")
    plt.title("Top 10 Brands by Product Count")
    plt.show()

    top_brands = df["brandName"].value_counts().head(5).index
    subset = df[df["brandName"].isin(top_brands)]

    plt.figure()
    subset.boxplot(
        column="pricing.finalPrice.value",
        by="brandName",
        rot=45
    )
    plt.xlabel("Brand")
    plt.ylabel("Final Price")
    plt.title("Price Distribution by Top Brands")
    plt.suptitle("")
    plt.show()

    plt.figure()
    df["product_type"].value_counts().plot(kind="pie", autopct="%1.1f%%")
    plt.ylabel("")
    plt.title("Product Type Proportion")
    plt.show()

    plt.figure()
    plt.violinplot(df["pricing.finalPrice.value"].dropna(), showmeans=True)
    plt.xlabel("Products")
    plt.ylabel("Final Price")
    plt.title("Violin Plot of Final Prices")
    plt.show()


def split_train_test(X, y, test_size=0.2, random_state=42):
    text.delete('1.0', END)
    global X_train, X_test, y_train, y_test

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    text.insert(END, f"X_train: {X_train.shape}, X_test: {X_test.shape}\n\n")
    text.insert(END, f"y_train: {y_train.shape}, y_test: {y_test.shape}\n\n")
    
    return X_train, X_test, y_train, y_test


import os
import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix, roc_curve, auc
)
from sklearn.preprocessing import label_binarize

# Ensure results folder exists
os.makedirs("results", exist_ok=True)

# Global DataFrame to store classification metrics
classification_metrics_df = pd.DataFrame(
    columns=['Algorithm', 'Accuracy', 'Precision', 'Recall', 'F1-Score']
)

def calculate_metrics(algorithm, y_pred, y_test, y_score=None):
   

    # -----------------------------
    # Load target label encoder (if exists)
    # -----------------------------
    encoder_path = os.path.join("models", "product_type_encoder.pkl")
    if os.path.exists(encoder_path):
        le_target = joblib.load(encoder_path)
        categories = le_target.classes_
    else:
        categories = np.unique(y_test)

    n_classes = len(categories)

    # -----------------------------
    # Classification Metrics
    # -----------------------------
    acc = accuracy_score(y_test, y_pred) * 100
    prec = precision_score(y_test, y_pred, average='macro', zero_division=0) * 100
    rec = recall_score(y_test, y_pred, average='macro', zero_division=0) * 100
    f1 = f1_score(y_test, y_pred, average='macro', zero_division=0) * 100

    global classification_metrics_df
    classification_metrics_df.loc[len(classification_metrics_df)] = [
        algorithm, acc, prec, rec, f1
    ]

    text.insert(END, f"\n{algorithm} Metrics\n\n")
    text.insert(END,"-" * 40)
    text.insert(END,f"Accuracy : {acc:.2f}%\n\n")
    text.insert(END,f"Precision: {prec:.2f}%\n\n")
    text.insert(END,f"Recall   : {rec:.2f}%\n\n")
    text.insert(END,f"F1-Score : {f1:.2f}%\n\n")

    text.insert(END,"\nClassification Report:")
    text.insert(END,
        classification_report(
            y_test,
            y_pred,
            labels=range(n_classes),
            target_names=categories,
            zero_division=0
        )
    )

    # -----------------------------
    # Confusion Matrix
    # -----------------------------
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(
        cm,
        annot=True,
        fmt="d",
        cmap="Blues",
        xticklabels=categories,
        yticklabels=categories
    )
    plt.title(f"{algorithm} - Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("True Label")
    plt.tight_layout()
    plt.savefig(f"results/{algorithm.replace(' ', '_')}_confusion_matrix.png")
    plt.show()

    # -----------------------------
    # ROC Curve
    # -----------------------------
    if y_score is not None:
        plt.figure(figsize=(10, 8))

        # -------- Binary classification --------
        if n_classes == 2:
            fpr, tpr, _ = roc_curve(y_test, y_score[:, 1])
            roc_auc = auc(fpr, tpr)
            plt.plot(fpr, tpr, lw=2, label=f"AUC = {roc_auc:.2f}")

        # -------- Multiclass classification --------
        else:
            y_test_bin = label_binarize(y_test, classes=range(n_classes))

            for i in range(n_classes):
                fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_score[:, i])
                roc_auc = auc(fpr, tpr)
                plt.plot(
                    fpr,
                    tpr,
                    lw=2,
                    label=f"{categories[i]} (AUC = {roc_auc:.2f})"
                )

        plt.plot([0, 1], [0, 1], "k--", lw=1)
        plt.xlabel("False Positive Rate")
        plt.ylabel("True Positive Rate")
        plt.title(f"{algorithm} - ROC Curve")
        plt.legend(loc="lower right")
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f"results/{algorithm.replace(' ', '_')}_roc_curve.png")
        plt.show()


from sklearn.ensemble import GradientBoostingClassifier
import os
import joblib

def train_gradient_boosting_classifier(
    X_train,
    y_train,
    X_test,
    y_test,
    learning_rate=0.01,
    n_estimators=100,
    max_depth=3,
    subsample=1.0,
    random_state=42
):
    text.delete('1.0', END)
    model_path = os.path.join(MODEL_DIR, "gradient_boosting_classifier.pkl")

    # -----------------------------
    # Load or Train
    # -----------------------------
    if os.path.exists(model_path):
        text.insert(END, "Loading Gradient Boosting Classifier...")
        model = joblib.load(model_path)
    else:
        text.insert(END,"Training Gradient Boosting Classifier...")
        model = GradientBoostingClassifier(
            learning_rate=learning_rate,
            n_estimators=n_estimators,
            max_depth=max_depth,
            subsample=subsample,
            random_state=random_state
        )
        model.fit(X_train, y_train)
        joblib.dump(model, model_path)
        text.insert(END,f"Model saved to {model_path}")

    # -----------------------------
    # Predictions
    # -----------------------------
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)

    # -----------------------------
    # Evaluation
    # -----------------------------
    calculate_metrics(
        algorithm="Gradient Boosting Classifier",
        y_pred=y_pred,
        y_test=y_test,
        y_score=y_score
    )

    return model


from lightgbm import LGBMClassifier
import os
import joblib

def train_lgbm_classifier(
    X_train,
    y_train,
    X_test,
    y_test,
    learning_rate=0.01,
    n_estimators=2,
    max_depth=-1,
    num_leaves=31,
    subsample=1.0,
    random_state=42
):

    text.delete('1.0', END)
    model_path = os.path.join(MODEL_DIR, "lgbm_classifier.pkl")

    # -----------------------------
    # Load or Train
    # -----------------------------
    if os.path.exists(model_path):
        text.insert(END,"Loading LGBM Classifier...")
        model = joblib.load(model_path)
    else:
        text.insert(END,"Training LGBM Classifier...")
        model = LGBMClassifier(
            learning_rate=learning_rate,
            n_estimators=n_estimators,
            max_depth=max_depth,
            num_leaves=num_leaves,
            subsample=subsample,
            random_state=random_state
        )
        model.fit(X_train, y_train)
        joblib.dump(model, model_path)
        text.insert(END,f"Model saved to {model_path}")

    # -----------------------------
    # Predictions
    # -----------------------------
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)

    # -----------------------------
    # Evaluation
    # -----------------------------
    calculate_metrics(
        algorithm="LGBM Classifier",
        y_pred=y_pred,
        y_test=y_test,
        y_score=y_score
    )

    return model

from ngboost import NGBClassifier
from ngboost.distns import k_categorical
from ngboost.scores import LogScore
import os
import joblib

def train_ngboost_classifier(
    X_train,
    y_train,
    X_test,
    y_test,
    n_estimators=2,
    learning_rate=0.01,
    minibatch_frac=1.0,
    col_sample=1.0,
    random_state=42,
    distribution=None,
    score=LogScore
):

    text.delete('1.0', END)
    
    model_path = os.path.join(MODEL_DIR, "ngboost_classifier.pkl")

    # -----------------------------
    # Load or Train
    # -----------------------------
    if os.path.exists(model_path):
        text.insert(END,"Loading NGBoost Classifier...")
        model = joblib.load(model_path)
    else:
        text.insert(END,"Training NGBoost Classifier...")

        # If distribution not provided, let NGBoost infer categorical from classes
        if distribution is None:
            # Use a categorical distribution with number of classes
            classes = len(set(y_train))
            distribution = k_categorical(classes)

        model = NGBClassifier(
            Dist=distribution,
            Score=score,
            n_estimators=n_estimators,
            learning_rate=learning_rate,
            minibatch_frac=minibatch_frac,
            col_sample=col_sample,
            random_state=random_state,
            verbose=False
        )

        model.fit(X_train, y_train)
        joblib.dump(model, model_path)
        text.insert(END,f"Model saved to {model_path}")

    # -----------------------------
    # Predictions
    # -----------------------------
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)

    # -----------------------------
    # Evaluation
    # -----------------------------
    calculate_metrics(
        algorithm="NGBoost Classifier",
        y_pred=y_pred,
        y_test=y_test,
        y_score=y_score
    )

    return model


from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
import os
import joblib

def train_calibrated_linearsvc_classifier(
    X_train,
    y_train,
    X_test,
    y_test,
    calibration_method='sigmoid',
    cv=5
):

    text.delete('1.0', END)
    model_path = os.path.join(MODEL_DIR, "calibrated_linearsvc.pkl")

    # -----------------------------
    # Load or Train
    # -----------------------------
    if os.path.exists(model_path):
        text.insert(END,"Loading Calibrated LinearSVC Classifier...")
        model = joblib.load(model_path)
    else:
        text.insert(END,"Training Calibrated LinearSVC Classifier...")

        base_svc = LinearSVC(
            max_iter=5000
        )

        model = CalibratedClassifierCV(
            estimator=base_svc,
            method=calibration_method,
            cv=cv
        )

        model.fit(X_train, y_train)
        joblib.dump(model, model_path)
        text.insert(END,f"Model saved to {model_path}")

    # -----------------------------
    # Predictions
    # -----------------------------
    y_pred = model.predict(X_test)
    y_score = model.predict_proba(X_test)

    # -----------------------------
    # Evaluation
    # -----------------------------
    calculate_metrics(
        algorithm="Calibrated LinearSVC",
        y_pred=y_pred,
        y_test=y_test,
        y_score=y_score
    )

    return model


def model_performance():
    global classification_metrics_df

    if classification_metrics_df.empty:
        messagebox.showwarning(
            "No Data",
            "Please train at least one model first."
        )
        return

    plt.figure(figsize=(8, 5))

    metrics = ['Accuracy', 'Precision', 'Recall', 'F1-Score']
    classification_metrics_df.set_index('Algorithm')[metrics].plot(kind='bar')

    plt.title("Model Performance Comparison")
    plt.ylabel("Score (%)")
    plt.xlabel("Model")
    plt.xticks(rotation=30, ha='right')
    plt.tight_layout()
    plt.show()


def predict_testdata():
    text.delete('1.0', END)

    # -----------------------------
    # Upload Test Dataset
    # -----------------------------
    file_path = filedialog.askopenfilename(
        title="Select Test Dataset",
        filetypes=[("CSV Files", "*.csv")]
    )

    if not file_path:
        text.insert(END, "No file selected.\n")
        return

    testdata = pd.read_csv(file_path)
    text.insert(END, f"Test data loaded from:\n{file_path}\n\n")

    # -----------------------------
    # Preprocess
    # -----------------------------
    X_test_new, _ = preprocess_data(testdata, is_train=False)

    # -----------------------------
    # Load Model & Encoder
    # -----------------------------
    target_le = joblib.load(
        os.path.join(MODEL_DIR, "product_type_encoder.pkl")
    )

    model = joblib.load(
        os.path.join(MODEL_DIR, "calibrated_linearsvc.pkl")
    )

    # -----------------------------
    # Prediction
    # -----------------------------
    preds = model.predict(X_test_new)
    preds_original = target_le.inverse_transform(preds)

    testdata['Prediction'] = preds_original

    # -----------------------------
    # Display Results
    # -----------------------------
    text.insert(END, "Prediction completed.\n\n")
    text.insert(END, testdata.head(10).to_string(index=False))
    text.insert(END, "\n\n")



def setBackground():
    global bg_photo
    image_path = r"BG_image\background.png" # Update with correct image path
    bg_image = Image.open(image_path)
    bg_image = bg_image.resize((screen_width, screen_height), Image.LANCZOS)
    #bg_image = bg_image.resize((900, 600), Image.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)
    bg_label = Label(main, image=bg_photo)
    bg_label.place(relwidth=1, relheight=1)

setBackground()


def connect_db():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["sparse_db"]
    return db


def signup(role):
    def register_user():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter all fields!")
            return

        try:
            db = connect_db()
            users = db.users

            # Check if user exists
            if users.find_one({"username": username, "role": role}):
                messagebox.showerror("Error", "User already exists!")
                return

            users.insert_one({
                "username": username,
                "password": password,
                "role": role
            })

            messagebox.showinfo("Success", f"{role} Signup Successful!")
            signup_window.destroy()

        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {e}")

    signup_window = tk.Toplevel(main)
    signup_window.geometry("400x300")
    signup_window.title(f"{role} Signup")

    Label(signup_window, text="Username").pack(pady=5)
    username_entry = tk.Entry(signup_window)
    username_entry.pack(pady=5)

    Label(signup_window, text="Password").pack(pady=5)
    password_entry = tk.Entry(signup_window, show="*")
    password_entry.pack(pady=5)

    tk.Button(signup_window, text="Signup", command=register_user).pack(pady=10)


# Login Functionality
def login(role):
    def verify_user():
        username = username_entry.get()
        password = password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter all fields!")
            return

        try:
            db = connect_db()
            users = db.users

            user = users.find_one({
                "username": username,
                "password": password,
                "role": role
            })

            if user:
                messagebox.showinfo("Success", f"{role} Login Successful!")
                login_window.destroy()

                if role == "Admin":
                    show_admin_buttons()
                else:
                    show_user_buttons()
            else:
                messagebox.showerror("Error", "Invalid Credentials!")

        except Exception as e:
            messagebox.showerror("Error", f"Database Error: {e}")

    login_window = tk.Toplevel(main)
    login_window.geometry("400x300")
    login_window.title(f"{role} Login")

    Label(login_window, text="Username").pack(pady=5)
    username_entry = tk.Entry(login_window)
    username_entry.pack(pady=5)

    Label(login_window, text="Password").pack(pady=5)
    password_entry = tk.Entry(login_window, show="*")
    password_entry.pack(pady=5)

    tk.Button(login_window, text="Login", command=verify_user).pack(pady=10)



# Clear buttons function
def clear_buttons():
    for widget in main.place_slaves():
        if isinstance(widget, tkinter.Button):
            widget.destroy()

# -----------------------------
# Admin Button Functions
# -----------------------------
def show_admin_buttons():
    font1 = ('times', 13, 'bold')
    clear_buttons()

    tk.Button(main, text="Upload Dataset", 
              command=uploadDataset, 
              font=font1, bg='#AF7AC5', fg='white').place(x=60, y=150)

    tk.Button(main, text="Preprocess Dataset", 
              command=lambda: preprocess_data(dataset), 
              font=font1, bg='#AF7AC5', fg='white').place(x=200, y=150)

    tk.Button(main, text="Show EDA Image", 
              command=lambda: perform_eda(dataset), 
              font=font1, bg='#AF7AC5', fg='white').place(x=60, y=250)

    tk.Button(main, text="Train-Test-Split", 
              command=lambda: split_train_test(X, y), 
              font=font1, bg='#AF7AC5', fg='white').place(x=220, y=250)

    tk.Button(main, text="Train GradientBoosting", 
              command=lambda: train_gradient_boosting_classifier(X_train, y_train, X_test, y_test),
              font=font1, bg='#AF7AC5', fg='white').place(x=50, y=350)

    tk.Button(main, text="Train LGBMClassifier", 
              command=lambda: train_lgbm_classifier(X_train, y_train, X_test, y_test),
              font=font1, bg='#AF7AC5', fg='white').place(x=290, y=350)

    tk.Button(main, text="Train NGBoostClassifier", 
              command=lambda: train_ngboost_classifier(X_train, y_train, X_test, y_test),
              font=font1, bg='#AF7AC5', fg='white').place(x=50, y=450)

    tk.Button(main, text="Train Calibrated LinearSVC", 
              command=lambda: train_calibrated_linearsvc_classifier(X_train, y_train, X_test, y_test),
              font=font1, bg='#AF7AC5', fg='white').place(x=290, y=450)

    tk.Button(main, text="Model Comparison",
                command=model_performance,
                font=font1, bg='#AF7AC5', fg='white').place(x=60, y=550)

    tk.Button(main, text="Logout", 
              command=show_login_screen, 
              font=font1, bg="red").place(x=250, y=550)



# -----------------------------
# User Button Functions
# -----------------------------
def show_user_buttons():
    font1 = ('times', 13, 'bold')
    clear_buttons()

    tk.Button(main, text="Upload Test Data", 
              command=predict_testdata,  
              font=font1, bg='#F4D03F', fg='black').place(x=60, y=300)

    tk.Button(main, text="Exit", 
              command=close, 
              font=font1, bg='#F4D03F', fg='black').place(x=60, y=350)

    tk.Button(main, text="Logout", 
              command=show_login_screen, 
              font=font1, bg="red").place(x=60, y=400)


def show_login_screen():
    clear_buttons()
    font1 = ('times', 14, 'bold')

    tk.Button(main, text="Admin Signup", command=lambda: signup("Admin"), font=font1, width=20, height=1, bg='#2F4F4F', fg='white').place(x=100, y=100)
    tk.Button(main, text="User Signup", command=lambda: signup("User"), font=font1, width=20, height=1, bg='#2F4F4F', fg='white').place(x=400, y=100)
    tk.Button(main, text="Admin Login", command=lambda: login("Admin"), font=font1, width=20, height=1, bg='#4682B4', fg='white').place(x=700, y=100)
    tk.Button(main, text="User Login", command=lambda: login("User"), font=font1, width=20, height=1, bg='#4682B4', fg='white').place(x=1000, y=100)

def close():
    main.destroy()


font = ('times', 16, 'bold')
title = Label(
    main,
    text="Multi-modal Product Recommendation System using Pricing, Brand, and Description Feature Fusion",
    bg='#4A235A', 
    fg='#E8F8F5',
    font=font,
    height=3,
    width=120
)
title.pack(pady=10)


                     
font1 = ('times', 12, 'bold')
text=Text(main,height=20,width=100)
scroll=Scrollbar(text)
text.configure(yscrollcommand=scroll.set)
text.place(x=600,y=420)
text.config(font=font1) 


# Admin and User Buttons
font1 = ('times', 14, 'bold')


tk.Button(main, text="Admin Signup", command=lambda: signup("Admin"), font=font1, width=20, height=1, bg='#2F4F4F', fg='white').place(x=100, y=100)

tk.Button(main, text="User Signup", command=lambda: signup("User"), font=font1, width=20, height=1, bg='#2F4F4F', fg='white').place(x=400, y=100)


admin_button = tk.Button(main, text="Admin Login", command=lambda: login("Admin"), font=font1, width=20, height=1, bg='#4682B4', fg='white')
admin_button.place(x=700, y=100)

user_button = tk.Button(main, text="User Login", command=lambda: login("User"), font=font1, width=20, height=1, bg='#4682B4', fg='white')
user_button.place(x=1000, y=100)

main.mainloop()



