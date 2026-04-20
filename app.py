import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from dotenv import load_dotenv

from voting import vote
from integrity import verify_chain, rebuild_chain
from database import (
    read_voters,
    get_voter_stats,
    import_voters_from_txt,
    mask_tc,
    read_ballots,
    reset_all_election_data
)
from crypto_utils import decrypt_vote, verify_text_hash
from audit_log import add_log, format_logs_for_display, verify_log_chain

load_dotenv()

BG_MAIN = "#0b1220"
BG_TOP = "#162338"
ACCENT = "#26c6ff"
TEXT = "#ffffff"
TEXT_SOFT = "#b8c7dc"
BTN_DARK = "#23344d"
BTN_RED = "#8e1b1b"
BTN_GREEN = "#0f7b3d"
BORDER = "#5a6e87"



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


def build_results_text(results: dict) -> str:
    stats = get_voter_stats()
    total_votes = sum(results.values())

    lines = []
    lines.append("=== SEÇİM SONUÇLARI ===\n")
    lines.append(f"Toplam Kayıtlı Seçmen : {stats['toplam_secmen']}")
    lines.append(f"Oy Kullanan          : {stats['oy_kullanan']}")
    lines.append(f"Oy Kullanmayan       : {stats['oy_kullanmayan']}")
    lines.append(f"Katılım Oranı        : %{stats['oy_kullanan_yuzde']}\n")

    if total_votes == 0:
        lines.append("Henüz geçerli oy yok.")
        return "\n".join(lines)

    lines.append("Parti Bazlı Dağılım:")
    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)

    for party, count in sorted_results:
        pct = round((count / total_votes) * 100, 2) if total_votes > 0 else 0
        lines.append(f"- {party}: {count} oy (%{pct})")

    winner_party, winner_count = sorted_results[0]
    winner_pct = round((winner_count / total_votes) * 100, 2) if total_votes > 0 else 0

    lines.append("")
    lines.append(f"Kazanan             : {winner_party}")
    lines.append(f"Kazanan Oy Sayısı   : {winner_count}")
    lines.append(f"Kazanan Oy Oranı    : %{winner_pct}")

    return "\n".join(lines)


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

    tk.Label(
        form_frame,
        text="TC Kimlik No:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    ).grid(row=0, column=0, padx=10, pady=12, sticky="e")

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

    tk.Label(
        form_frame,
        text="Oy Tercihi:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    ).grid(row=1, column=0, padx=10, pady=12, sticky="e")

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
            add_log("OY", f"Oy kullanıldı: {mask_tc(tc)}")
            messagebox.showinfo("Başarılı", message)
            tc_entry.delete(0, tk.END)
            vote_combo.set("")
        else:
            masked = mask_tc(tc) if tc.isdigit() and len(tc) == 11 else "geçersiz_tc"
            add_log("HATA", f"Oy verme başarısız: {masked} | {message}")
            messagebox.showerror("Hata", message)

    tk.Button(
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
    ).pack(pady=25)


def open_admin_login_window():
    login_window = tk.Toplevel(root)
    login_window.title("Seçim Kurulu Girişi")
    login_window.geometry("430x280")
    login_window.configure(bg=BG_MAIN)
    login_window.resizable(False, False)

    tk.Label(
        login_window,
        text="SEÇİM KURULU GİRİŞİ",
        font=("Arial", 18, "bold"),
        fg=ACCENT,
        bg=BG_MAIN
    ).pack(pady=20)

    form_frame = tk.Frame(login_window, bg=BG_MAIN)
    form_frame.pack(pady=15)

    tk.Label(
        form_frame,
        text="Kullanıcı Adı:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    ).grid(row=0, column=0, padx=10, pady=10, sticky="e")

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

    tk.Label(
        form_frame,
        text="Şifre:",
        font=("Arial", 12, "bold"),
        fg=TEXT,
        bg=BG_MAIN
    ).grid(row=1, column=0, padx=10, pady=10, sticky="e")

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
            add_log("HATA", "Admin bilgileri .env içinde eksik.")
            messagebox.showerror("Hata", ".env içinde admin bilgileri eksik.")
            return

        if username == admin_username and verify_text_hash(password, admin_password_hash):
            add_log("ADMIN", "Yönetici girişi yapıldı.")
            messagebox.showinfo("Başarılı", "Admin girişi başarılı.")
            login_window.destroy()
            open_admin_panel()
        else:
            add_log("UYARI", f"Başarısız admin giriş denemesi: kullanıcı={username}")
            messagebox.showerror("Hata", "Kullanıcı adı veya şifre yanlış.")

    tk.Button(
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
    ).pack(pady=20)

def open_admin_panel():
    admin_window = tk.Toplevel(root)
    admin_window.title("CryptoVote - Seçim Kurulu Denetim Merkezi")
    admin_window.geometry("1220x900")
    admin_window.configure(bg=BG_MAIN)
    admin_window.resizable(False, False)

    top_frame = tk.Frame(admin_window, bg=BG_TOP, height=95)
    top_frame.pack(fill="x")
    top_frame.pack_propagate(False)

    tk.Label(
        top_frame,
        text="🛡️",
        font=("Arial", 26),
        bg=BG_TOP,
        fg=TEXT
    ).pack(side="left", padx=(28, 14), pady=18)

    tk.Label(
        top_frame,
        text="CRYPTOVOTE",
        font=("Arial", 30, "bold"),
        bg=BG_TOP,
        fg=ACCENT
    ).pack(side="left", pady=18)

    sub_bar = tk.Frame(admin_window, bg="#0a1424", height=48)
    sub_bar.pack(fill="x")
    sub_bar.pack_propagate(False)

    tk.Label(
        sub_bar,
        text="📊 SEÇİM KURULU DENETİM MERKEZİ",
        font=("Arial", 16, "bold"),
        bg="#0a1424",
        fg=ACCENT
    ).pack(pady=10)

    content_frame = tk.Frame(admin_window, bg=BG_MAIN)
    content_frame.pack(fill="both", expand=True, padx=16, pady=14)

    # TABLO
    table_frame = tk.Frame(content_frame, bg=BG_MAIN)
    table_frame.pack(fill="x", pady=(0, 10))

    columns = ("tc_maskeli", "durum")
    secmen_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=8)
    secmen_tree.heading("tc_maskeli", text="T.C. Kimlik (Maskelenmiş)")
    secmen_tree.heading("durum", text="Oy Durumu")
    secmen_tree.column("tc_maskeli", width=540, anchor="center")
    secmen_tree.column("durum", width=540, anchor="center")

    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass

    style.configure(
        "Treeview",
        background="#f0f0f0",
        foreground="black",
        rowheight=28,
        fieldbackground="#f0f0f0",
        bordercolor=BORDER,
        borderwidth=1,
        font=("Arial", 11)
    )
    style.configure(
        "Treeview.Heading",
        background="#d8d8d8",
        foreground="black",
        font=("Arial", 12, "bold")
    )

    secmen_tree.pack(fill="x")

    # BUTONLAR
    button_frame = tk.Frame(content_frame, bg=BG_MAIN)
    button_frame.pack(fill="x", pady=(4, 10))

    # SONUÇ KUTUSU
    result_box = tk.Text(
        content_frame,
        height=14,
        width=120,
        font=("Consolas", 11),
        bg="#020913",
        fg="#8cf0ff",
        relief="flat",
        bd=1,
        highlightthickness=1,
        highlightbackground=BORDER,
        insertbackground=TEXT
    )
    result_box.pack(fill="both", expand=True, pady=(4, 10))

    def append_result(text: str):
        result_box.config(state="normal")
        result_box.delete("1.0", tk.END)
        result_box.insert(tk.END, text)
        result_box.config(state="disabled")

    def refresh_stats_and_table():
        for item in secmen_tree.get_children():
            secmen_tree.delete(item)

        voters = read_voters()
        for voter in voters:
            secmen_tree.insert(
                "",
                "end",
                values=(
                    mask_tc(voter["tc"]),
                    "✓ OY VERDİ" if voter.get("oy_kullandi") else "✗ VERMEDİ"
                )
            )

    def tc_listesini_aktar():
        file_path = filedialog.askopenfilename(
            title="TC Listesi Seç",
            filetypes=[("Metin Dosyaları", "*.txt")]
        )
        if not file_path:
            return

        success, message = import_voters_from_txt(file_path)
        if success:
            add_log("IMPORT", f"TC listesi aktarıldı: {os.path.basename(file_path)} | {message}")
            refresh_stats_and_table()
            append_result("TC listesi başarıyla sisteme aktarıldı.\n\n" + message)
            messagebox.showinfo("Başarılı", message)
        else:
            add_log("HATA", f"TC listesi aktarımı başarısız: {message}")
            messagebox.showerror("Hata", message)

    def guvenlik_loglarini_goster():
        add_log("LOG", "Loglar görüntülendi.")
        append_result(format_logs_for_display())

    def zinciri_yeniden_olustur():
        success, message = rebuild_chain()
        if success:
            add_log("ZINCIR", "Hash zinciri yeniden oluşturuldu.")
            append_result(message)
            messagebox.showinfo("Başarılı", message)
        else:
            add_log("HATA", f"Hash zinciri yeniden oluşturulamadı: {message}")
            messagebox.showerror("Hata", message)

    def tum_sistemi_sifirla():
        answer = messagebox.askyesno(
            "Onay",
            "Bu işlem TEST MODU içindir.\n\n"
            "Seçmen oy durumları ve sandık kayıtları sıfırlanacaktır.\n"
            "Devam etmek istiyor musunuz?"
        )
        if not answer:
            return

        second = messagebox.askyesno(
            "Son Onay",
            "Bu işlem geri alınamaz.\n"
            "Sistem sıfırlansın mı?"
        )
        if not second:
            return

        try:
            reset_all_election_data()
            add_log("RESET", "Sistem sıfırlandı (tüm oylar temizlendi).")
            refresh_stats_and_table()
            append_result("Sistem sıfırlandı.\nTüm oy durumları temizlendi, sandık boşaltıldı.")
            messagebox.showinfo("Başarılı", "Sistem başarıyla sıfırlandı.")
        except Exception as e:
            add_log("HATA", f"Sistem sıfırlama başarısız: {e}")
            messagebox.showerror("Hata", f"Sistem sıfırlanamadı:\n{e}")

    def sandigi_ac_ve_sayimi_baslat():
        if not verify_log_chain():
            add_log("UYARI", "Sandık açma reddedildi: log zinciri bozuk.")
            append_result("❌ Adli bilişim log zinciri bozulmuş.\nSandık açılamaz.")
            return

        if not verify_chain():
            add_log("UYARI", "Sandık açma reddedildi: hash zinciri bozuk.")
            append_result("❌ Veri bütünlüğü bozulmuş.\nSandık açılamaz.")
            return

        results, status = count_votes()

        if results is None:
            add_log("HATA", f"Sandık açma başarısız: {status}")
            append_result(f"❌ {status}")
            return

        if not results:
            add_log("BILGI", "Sandık açıldı ancak sandık boş.")
            append_result("Sandık boş.")
            return

        add_log("SANDIK", "Sandık açıldı ve sayım yapıldı.")
        append_result(build_results_text(results))

    def ana_menuye_don():
        admin_window.destroy()

    tk.Button(
        button_frame,
        text="📂 T.C. LİSTESİNİ SİSTEME AKTAR",
        command=tc_listesini_aktar,
        font=("Arial", 12, "bold"),
        bg=BTN_DARK,
        fg=ACCENT,
        activebackground="#334766",
        activeforeground=ACCENT,
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="🕵️ GÜVENLİK LOGLARI (ADLİ BİLİŞİM)",
        command=guvenlik_loglarini_goster,
        font=("Arial", 12, "bold"),
        bg=BTN_DARK,
        fg=TEXT_SOFT,
        activebackground="#334766",
        activeforeground=TEXT,
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="🔁 HASH ZİNCİRİNİ YENİDEN OLUŞTUR",
        command=zinciri_yeniden_olustur,
        font=("Arial", 12, "bold"),
        bg=BTN_GREEN,
        fg="white",
        activebackground="#14914a",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="⚠ TÜM SİSTEMİ SIFIRLA (TEST MODU)",
        command=tum_sistemi_sifirla,
        font=("Arial", 12, "bold"),
        bg=BTN_RED,
        fg="white",
        activebackground="#b32020",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="🔓 SANDIĞI AÇ VE SAYIMI BAŞLAT",
        command=sandigi_ac_ve_sayimi_baslat,
        font=("Arial", 14, "bold"),
        bg=BTN_DARK,
        fg="#4cff8f",
        activebackground="#334766",
        activeforeground="#4cff8f",
        relief="flat",
        cursor="hand2",
        height=2
    ).pack(fill="x", pady=(6, 0))

    tk.Button(
        content_frame,
        text="⬅ ANA MENÜ",
        command=ana_menuye_don,
        font=("Arial", 12, "bold"),
        bg="#3a4b66",
        fg="white",
        activebackground="#50627f",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=(8, 0))

    refresh_stats_and_table()
    append_result(
        "Sistem hazır.\n\n"
        "- TC listesini içe aktar\n"
        "- Güvenlik loglarını görüntüle\n"
        "- Gerekirse hash zincirini yeniden oluştur\n"
        "- Sandığı aç ve sayımı başlat"
    )


def sandigi_ac_ve_sayimi_baslat():
    if not verify_log_chain():
        add_log("UYARI", "Sandık açma reddedildi: log zinciri bozuk.")
        append_result("❌ Adli bilişim log zinciri bozulmuş.\nSandık açılamaz.")
        return

    if not verify_chain():
        add_log("UYARI", "Sandık açma reddedildi: hash zinciri bozuk.")
        append_result("❌ Veri bütünlüğü bozulmuş.\nSandık açılamaz.")
        return

    results, status = count_votes()

    if results is None:
        add_log("HATA", f"Sandık açma başarısız: {status}")
        append_result(f"❌ {status}")
        return

    if not results:
        add_log("BILGI", "Sandık açıldı ancak sandık boş.")
        append_result("Sandık boş.")
        return

    add_log("SANDIK", "Sandık açıldı ve sayım yapıldı.")
    append_result(build_results_text(results))	

    def ana_menuye_don():
        admin_window.destroy()

    tk.Button(
        button_frame,
        text="📂 T.C. LİSTESİNİ SİSTEME AKTAR",
        command=tc_listesini_aktar,
        font=("Arial", 12, "bold"),
        bg=BTN_DARK,
        fg=ACCENT,
        activebackground="#334766",
        activeforeground=ACCENT,
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="🕵️ SİSTEM LOGLARINI GÖSTER",
        command=guvenlik_loglarini_goster,
        font=("Arial", 12, "bold"),
        bg=BTN_DARK,
        fg=TEXT_SOFT,
        activebackground="#334766",
        activeforeground=TEXT,
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="🔁 HASH ZİNCİRİNİ YENİDEN OLUŞTUR",
        command=zinciri_yeniden_olustur,
        font=("Arial", 12, "bold"),
        bg=BTN_GREEN,
        fg="white",
        activebackground="#14914a",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="⚠ TÜM SİSTEMİ SIFIRLA (TEST MODU)",
        command=tum_sistemi_sifirla,
        font=("Arial", 12, "bold"),
        bg=BTN_RED,
        fg="white",
        activebackground="#b32020",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=3)

    tk.Button(
        button_frame,
        text="🔓 SANDIĞI AÇ VE SAYIMI BAŞLAT",
        command=sandigi_ac_ve_sayimi_baslat,
        font=("Arial", 14, "bold"),
        bg=BTN_DARK,
        fg="#4cff8f",
        activebackground="#334766",
        activeforeground="#4cff8f",
        relief="flat",
        cursor="hand2",
        height=2
    ).pack(fill="x", pady=(6, 0))

    tk.Button(
        content_frame,
        text="⬅ ANA MENÜ",
        command=ana_menuye_don,
        font=("Arial", 12, "bold"),
        bg="#3a4b66",
        fg="white",
        activebackground="#50627f",
        activeforeground="white",
        relief="flat",
        cursor="hand2",
        height=1
    ).pack(fill="x", pady=(8, 0))

    refresh_stats_and_table()
    append_result(
        "Sistem hazır.\n\n"
        "- TC listesini içe aktar\n"
        "- Logları görüntüle\n"
        "- Gerekirse hash zincirini yeniden oluştur\n"
        "- Sandığı aç ve sayımı başlat"
    )


root = tk.Tk()
root.title("CryptoVote - Secure Voting System")
root.geometry("540x620")
root.configure(bg=BG_MAIN)
root.resizable(False, False)

top_frame = tk.Frame(root, bg=BG_TOP, height=110)
top_frame.pack(fill="x")
top_frame.pack_propagate(False)

tk.Label(
    top_frame,
    text="🛡️",
    font=("Arial", 34),
    bg=BG_TOP,
    fg=TEXT
).pack(side="left", padx=(95, 12), pady=20)

tk.Label(
    top_frame,
    text="CRYPTOVOTE",
    font=("Arial", 28, "bold"),
    bg=BG_TOP,
    fg=ACCENT
).pack(side="left", pady=24)

tk.Frame(root, bg=ACCENT, height=2).pack(fill="x")

tk.Label(
    root,
    text="Güvenli Oylama Sistemine Hoş Geldiniz",
    font=("Arial", 15),
    bg=BG_MAIN,
    fg=TEXT
).pack(pady=(110, 35))

tk.Button(
    root,
    text="🗳 OY KULLANMA PANELİ",
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
).pack(pady=12)

tk.Button(
    root,
    text="🏛 SEÇİM KURULU GİRİŞİ",
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
).pack(pady=12)

tk.Label(
    root,
    text="Sistem Durumu: ÇALIŞIYOR | AES Aktif | Admin Korumalı",
    font=("Arial", 11),
    bg=BG_MAIN,
    fg="#5f5f66"
).pack(side="bottom", pady=24)

add_log("SISTEM", "Uygulama başlatıldı.")
root.mainloop()
