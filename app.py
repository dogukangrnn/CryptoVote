import os
import tkinter as tk
from tkinter import ttk, messagebox
from dotenv import load_dotenv

from voting import vote
from integrity import verify_chain
from database import (
    read_ballots,
    add_voter,
    delete_voter,
    update_voter,
    get_voter_stats,
    list_voters
)
from crypto_utils import decrypt_vote, verify_text_hash

load_dotenv()

BG_MAIN = "#0b0b0f"
BG_TOP = "#1a1a1f"
ACCENT = "#19d3ff"
TEXT = "#ffffff"
TEXT_SOFT = "#bfbfbf"
BTN_DARK = "#2a2a2f"
BOX_BG = "#121218"


def count_votes():
    if not verify_chain():
        return None, "Veri bütünlüğü bozulmuş. Sandık açılamaz."

    ballots = read_ballots()

    if not ballots:
        return {}, "Sandık boş."

    results = {}

    for ballot in ballots:
        try:
            solved_vote = decrypt_vote(ballot["encrypted_vote"])
            results[solved_vote] = results.get(solved_vote, 0) + 1
        except Exception as e:
            return None, f"Oy çözme hatası: {e}"

    return results, "Başarılı"


def build_stats_text():
    stats = get_voter_stats()
    return (
        f"Toplam Kayıtlı Seçmen: {stats['toplam_secmen']}\n"
        f"Oy Kullanan: {stats['oy_kullanan']} (%{stats['oy_kullanan_yuzde']})\n"
        f"Oy Kullanmayan: {stats['oy_kullanmayan']} (%{stats['oy_kullanmayan_yuzde']})"
    )


def open_vote_window():
    vote_window = tk.Toplevel(root)
    vote_window.title("Oy Kullanma Paneli")
    vote_window.geometry("520x360")
    vote_window.configure(bg=BG_MAIN)
    vote_window.resizable(False, False)

    title = tk.Label(
        vote_window,
        text="OY KULLANMA PANELİ",
        font=("Arial", 18, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    title.pack(pady=20)

    form_frame = tk.Frame(vote_window, bg=BG_MAIN)
    form_frame.pack(pady=20)

    tc_label = tk.Label(
        form_frame,
        text="TC Kimlik No:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    )
    tc_label.grid(row=0, column=0, padx=10, pady=12, sticky="e")

    tc_entry = tk.Entry(
        form_frame,
        width=28,
        font=("Arial", 12),
        bg="#1e1e24",
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat"
    )
    tc_entry.grid(row=0, column=1, padx=10, pady=12)

    vote_label = tk.Label(
        form_frame,
        text="Oy Tercihi:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    )
    vote_label.grid(row=1, column=0, padx=10, pady=12, sticky="e")

    vote_var = tk.StringVar()
    vote_combo = ttk.Combobox(
        form_frame,
        textvariable=vote_var,
        values=["A Partisi", "B Partisi", "C Partisi"],
        state="readonly",
        width=25,
        font=("Arial", 12)
    )
    vote_combo.grid(row=1, column=1, padx=10, pady=12)

    def submit_vote():
        tc = tc_entry.get().strip()
        selected_vote = vote_var.get().strip()

        if not tc or not selected_vote:
            messagebox.showwarning("Eksik Bilgi", "TC Kimlik No ve oy tercihi girilmelidir.")
            return

        success, message = vote(tc, selected_vote)

        if success:
            messagebox.showinfo("Başarılı", message)
            tc_entry.delete(0, tk.END)
            vote_combo.set("")
        else:
            messagebox.showerror("Hata", message)

    vote_button = tk.Button(
        vote_window,
        text="OY VER",
        command=submit_vote,
        font=("Arial", 13, "bold"),
        bg=ACCENT,
        fg="black",
        activebackground="#47ddff",
        activeforeground="black",
        width=18,
        height=1,
        relief="flat",
        cursor="hand2"
    )
    vote_button.pack(pady=25)


def open_admin_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("Seçim Kurulu Girişi")
    login_window.geometry("430x280")
    login_window.configure(bg=BG_MAIN)
    login_window.resizable(False, False)

    title = tk.Label(
        login_window,
        text="SEÇİM KURULU GİRİŞİ",
        font=("Arial", 18, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    title.pack(pady=20)

    form_frame = tk.Frame(login_window, bg=BG_MAIN)
    form_frame.pack(pady=15)

    user_label = tk.Label(
        form_frame,
        text="Kullanıcı Adı:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    )
    user_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

    user_entry = tk.Entry(
        form_frame,
        width=25,
        font=("Arial", 12),
        bg="#1e1e24",
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat"
    )
    user_entry.grid(row=0, column=1, padx=10, pady=10)

    pass_label = tk.Label(
        form_frame,
        text="Şifre:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    )
    pass_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")

    pass_entry = tk.Entry(
        form_frame,
        width=25,
        font=("Arial", 12),
        bg="#1e1e24",
        fg=TEXT,
        insertbackground=TEXT,
        relief="flat",
        show="*"
    )
    pass_entry.grid(row=1, column=1, padx=10, pady=10)

    def login_admin():
        username = user_entry.get().strip()
        password = pass_entry.get().strip()

        admin_username = os.getenv("ADMIN_USERNAME")
        admin_password_hash = os.getenv("ADMIN_PASSWORD_HASH")

        if not admin_username or not admin_password_hash:
            messagebox.showerror("Hata", ".env içinde admin bilgileri eksik.")
            return

        if username == admin_username and verify_text_hash(password, admin_password_hash):
            messagebox.showinfo("Başarılı", "Admin girişi başarılı.")
            login_window.destroy()
            open_admin_panel()
        else:
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış.")

    login_button = tk.Button(
        login_window,
        text="GİRİŞ YAP",
        command=login_admin,
        font=("Arial", 12, "bold"),
        bg=ACCENT,
        fg="black",
        activebackground="#47ddff",
        activeforeground="black",
        width=16,
        relief="flat",
        cursor="hand2"
    )
    login_button.pack(pady=20)


def open_admin_panel():
    admin_window = tk.Toplevel(root)
    admin_window.title("Seçim Kurulu Admin Paneli")
    admin_window.geometry("900x650")
    admin_window.configure(bg=BG_MAIN)
    admin_window.resizable(False, False)

    title = tk.Label(
        admin_window,
        text="SEÇİM KURULU ADMIN PANELİ",
        font=("Arial", 18, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    title.pack(pady=15)

    content_frame = tk.Frame(admin_window, bg=BG_MAIN)
    content_frame.pack(fill="both", expand=True, padx=15, pady=10)

    left_frame = tk.Frame(content_frame, bg=BG_MAIN)
    left_frame.pack(side="left", fill="y", padx=(0, 10))

    right_frame = tk.Frame(content_frame, bg=BG_MAIN)
    right_frame.pack(side="right", fill="both", expand=True)

    stats_label = tk.Label(
        left_frame,
        text="Sistem İstatistikleri",
        font=("Arial", 13, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    stats_label.pack(pady=(0, 8))

    stats_box = tk.Text(
        left_frame,
        height=6,
        width=34,
        font=("Consolas", 10),
        bg=BOX_BG,
        fg=TEXT,
        relief="flat"
    )
    stats_box.pack(pady=(0, 15))

    def refresh_stats():
        stats_box.config(state="normal")
        stats_box.delete("1.0", tk.END)
        stats_box.insert(tk.END, build_stats_text())
        stats_box.config(state="disabled")

    manage_label = tk.Label(
        left_frame,
        text="Seçmen Yönetimi",
        font=("Arial", 13, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    manage_label.pack(pady=(0, 8))

    form_frame = tk.Frame(left_frame, bg=BG_MAIN)
    form_frame.pack()

    add_label = tk.Label(form_frame, text="Yeni TC:", font=("Arial", 11), fg=TEXT, bg=BG_MAIN)
    add_label.grid(row=0, column=0, padx=6, pady=6, sticky="e")

    add_entry = tk.Entry(form_frame, width=20, font=("Arial", 11), bg="#1e1e24", fg=TEXT, insertbackground=TEXT)
    add_entry.grid(row=0, column=1, padx=6, pady=6)

    del_label = tk.Label(form_frame, text="Silinecek TC:", font=("Arial", 11), fg=TEXT, bg=BG_MAIN)
    del_label.grid(row=1, column=0, padx=6, pady=6, sticky="e")

    del_entry = tk.Entry(form_frame, width=20, font=("Arial", 11), bg="#1e1e24", fg=TEXT, insertbackground=TEXT)
    del_entry.grid(row=1, column=1, padx=6, pady=6)

    old_label = tk.Label(form_frame, text="Eski TC:", font=("Arial", 11), fg=TEXT, bg=BG_MAIN)
    old_label.grid(row=2, column=0, padx=6, pady=6, sticky="e")

    old_entry = tk.Entry(form_frame, width=20, font=("Arial", 11), bg="#1e1e24", fg=TEXT, insertbackground=TEXT)
    old_entry.grid(row=2, column=1, padx=6, pady=6)

    new_label = tk.Label(form_frame, text="Yeni TC:", font=("Arial", 11), fg=TEXT, bg=BG_MAIN)
    new_label.grid(row=3, column=0, padx=6, pady=6, sticky="e")

    new_entry = tk.Entry(form_frame, width=20, font=("Arial", 11), bg="#1e1e24", fg=TEXT, insertbackground=TEXT)
    new_entry.grid(row=3, column=1, padx=6, pady=6)

    def refresh_voter_list():
        voter_list_box.config(state="normal")
        voter_list_box.delete("1.0", tk.END)
        voters = list_voters()

        if not voters:
            voter_list_box.insert(tk.END, "Kayıtlı seçmen yok.\n")
        else:
            for i, voter in enumerate(voters, start=1):
                durum = "KULLANDI" if voter["oy_kullandi"] else "KULLANMADI"
                voter_list_box.insert(
                    tk.END,
                    f"{i}. TC: {voter['tc']} | Durum: {durum}\n"
                )

        voter_list_box.config(state="disabled")

    def admin_add_voter():
        tc = add_entry.get().strip()
        success, message = add_voter(tc)

        if success:
            messagebox.showinfo("Başarılı", message)
            add_entry.delete(0, tk.END)
            refresh_stats()
            refresh_voter_list()
        else:
            messagebox.showerror("Hata", message)

    def admin_delete_voter():
        tc = del_entry.get().strip()
        success, message = delete_voter(tc)

        if success:
            messagebox.showinfo("Başarılı", message)
            del_entry.delete(0, tk.END)
            refresh_stats()
            refresh_voter_list()
        else:
            messagebox.showerror("Hata", message)

    def admin_update_voter():
        old_tc = old_entry.get().strip()
        new_tc = new_entry.get().strip()
        success, message = update_voter(old_tc, new_tc)

        if success:
            messagebox.showinfo("Başarılı", message)
            old_entry.delete(0, tk.END)
            new_entry.delete(0, tk.END)
            refresh_stats()
            refresh_voter_list()
        else:
            messagebox.showerror("Hata", message)

    button_manage_frame = tk.Frame(left_frame, bg=BG_MAIN)
    button_manage_frame.pack(pady=10)

    add_button = tk.Button(
        button_manage_frame,
        text="KİŞİ EKLE",
        command=admin_add_voter,
        font=("Arial", 10, "bold"),
        bg=ACCENT,
        fg="black",
        relief="flat",
        width=12,
        cursor="hand2"
    )
    add_button.grid(row=0, column=0, padx=5, pady=5)

    delete_button = tk.Button(
        button_manage_frame,
        text="KİŞİ SİL",
        command=admin_delete_voter,
        font=("Arial", 10, "bold"),
        bg="#ff5f5f",
        fg="black",
        relief="flat",
        width=12,
        cursor="hand2"
    )
    delete_button.grid(row=0, column=1, padx=5, pady=5)

    update_button = tk.Button(
        button_manage_frame,
        text="DÜZENLE",
        command=admin_update_voter,
        font=("Arial", 10, "bold"),
        bg="#ffd166",
        fg="black",
        relief="flat",
        width=12,
        cursor="hand2"
    )
    update_button.grid(row=0, column=2, padx=5, pady=5)

    right_top_label = tk.Label(
        right_frame,
        text="Kurul İşlemleri ve Seçmen Listesi",
        font=("Arial", 13, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    right_top_label.pack(pady=(0, 8))

    board_result_box = tk.Text(
        right_frame,
        height=14,
        width=62,
        font=("Consolas", 10),
        bg=BOX_BG,
        fg=TEXT,
        relief="flat"
    )
    board_result_box.pack(pady=(0, 12))

    def check_integrity_gui():
        board_result_box.config(state="normal")
        board_result_box.delete("1.0", tk.END)

        if verify_chain():
            board_result_box.insert(tk.END, "✅ Hash zinciri sağlam.\n")
        else:
            board_result_box.insert(tk.END, "❌ Veri bütünlüğü bozulmuş.\n")

        board_result_box.config(state="disabled")

    def show_results_gui():
        board_result_box.config(state="normal")
        board_result_box.delete("1.0", tk.END)

        results, status = count_votes()

        if results is None:
            board_result_box.insert(tk.END, f"❌ {status}\n")
            board_result_box.config(state="disabled")
            return

        if not results:
            board_result_box.insert(tk.END, "Sandık boş.\n")
            board_result_box.config(state="disabled")
            return

        board_result_box.insert(tk.END, "=== SEÇİM SONUÇLARI ===\n\n")
        for party, count in results.items():
            board_result_box.insert(tk.END, f"{party}: {count} oy\n")

        board_result_box.config(state="disabled")

    board_button_frame = tk.Frame(right_frame, bg=BG_MAIN)
    board_button_frame.pack(pady=(0, 12))

    integrity_button = tk.Button(
        board_button_frame,
        text="ZİNCİRİ DOĞRULA",
        command=check_integrity_gui,
        font=("Arial", 10, "bold"),
        bg=BTN_DARK,
        fg=TEXT,
        relief="flat",
        width=18,
        cursor="hand2"
    )
    integrity_button.grid(row=0, column=0, padx=8)

    result_button = tk.Button(
        board_button_frame,
        text="SONUÇLARI GÖSTER",
        command=show_results_gui,
        font=("Arial", 10, "bold"),
        bg=ACCENT,
        fg="black",
        relief="flat",
        width=18,
        cursor="hand2"
    )
    result_button.grid(row=0, column=1, padx=8)

    voter_list_label = tk.Label(
        right_frame,
        text="Kayıtlı Seçmen Listesi",
        font=("Arial", 12, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    )
    voter_list_label.pack(pady=(5, 8))

    voter_list_box = tk.Text(
        right_frame,
        height=12,
        width=62,
        font=("Consolas", 10),
        bg=BOX_BG,
        fg=TEXT,
        relief="flat"
    )
    voter_list_box.pack()

    refresh_stats()
    refresh_voter_list()


root = tk.Tk()
root.title("CryptoVote v1.0 - Secure Systems")
root.geometry("480x580")
root.configure(bg=BG_MAIN)
root.resizable(False, False)

top_frame = tk.Frame(root, bg=BG_TOP, height=110)
top_frame.pack(fill="x")
top_frame.pack_propagate(False)

logo_label = tk.Label(
    top_frame,
    text="🛡️",
    font=("Arial", 34),
    bg=BG_TOP,
    fg=TEXT
)
logo_label.pack(side="left", padx=(85, 10), pady=20)

title_label = tk.Label(
    top_frame,
    text="CRYPTOVOTE",
    font=("Arial", 28, "bold"),
    bg=BG_TOP,
    fg=ACCENT
)
title_label.pack(side="left", pady=24)

line = tk.Frame(root, bg=ACCENT, height=2)
line.pack(fill="x")

welcome_label = tk.Label(
    root,
    text="Güvenli Oylama Sistemine Hoş Geldiniz",
    font=("Arial", 15),
    bg=BG_MAIN,
    fg=TEXT
)
welcome_label.pack(pady=(110, 35))

vote_btn = tk.Button(
    root,
    text="📦 OY KULLANMA PANELİ",
    command=open_vote_window,
    font=("Arial", 14, "bold"),
    bg="#20c8ee",
    fg="black",
    activebackground="#47ddff",
    activeforeground="black",
    width=24,
    height=2,
    relief="flat",
    cursor="hand2"
)
vote_btn.pack(pady=12)

board_btn = tk.Button(
    root,
    text="🔐 SEÇİM KURULU GİRİŞİ",
    command=open_admin_login_window,
    font=("Arial", 14, "bold"),
    bg=BTN_DARK,
    fg=TEXT,
    activebackground="#3b3b42",
    activeforeground=TEXT,
    width=24,
    height=2,
    relief="flat",
    cursor="hand2",
    highlightthickness=1,
    highlightbackground="#9a9a9a"
)
board_btn.pack(pady=12)

status_label = tk.Label(
    root,
    text="Sistem Durumu: ÇALIŞIYOR | AES-256 Aktif | Admin Korumalı",
    font=("Arial", 11),
    bg=BG_MAIN,
    fg="#5f5f66"
)
status_label.pack(side="bottom", pady=24)

root.mainloop()
