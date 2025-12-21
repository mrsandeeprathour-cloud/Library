# library_lms.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import mysql.connector
from mysql.connector import errorcode
from datetime import datetime, timedelta

# ---------------------- Database helper ----------------------
class DB:
    def __init__(self):
        self.conn = None
        self.cursor = None

    def connect(self, host, user, password, database):
        try:
            # try connecting to given database; if database doesn't exist, create it
            self.conn = mysql.connector.connect(host=host, user=user, password=password)
            self.cursor = self.conn.cursor()
            self.cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database}` DEFAULT CHARACTER SET 'utf8mb4'")
            self.conn.database = database
            self._create_tables()
            return True, "Connected and database ready."
        except mysql.connector.Error as err:
            return False, f"DB Error: {err}"

    def _create_tables(self):
        # Create required tables if they're not present
        tables = {}
        tables['books'] = (
            "CREATE TABLE IF NOT EXISTS books ("
            " id INT AUTO_INCREMENT PRIMARY KEY,"
            " title VARCHAR(255) NOT NULL,"
            " author VARCHAR(255),"
            " year INT,"
            " isbn VARCHAR(50),"
            " copies INT DEFAULT 1,"
            " UNIQUE (isbn)"
            ") ENGINE=InnoDB"
        )
        tables['students'] = (
            "CREATE TABLE IF NOT EXISTS students ("
            " id INT AUTO_INCREMENT PRIMARY KEY,"
            " name VARCHAR(255) NOT NULL,"
            " roll VARCHAR(100) UNIQUE,"
            " email VARCHAR(255),"
            " phone VARCHAR(50)"
            ") ENGINE=InnoDB"
        )
        tables['issues'] = (
            "CREATE TABLE IF NOT EXISTS issues ("
            " id INT AUTO_INCREMENT PRIMARY KEY,"
            " book_id INT NOT NULL,"
            " student_id INT NOT NULL,"
            " issue_date DATE NOT NULL,"
            " due_date DATE NOT NULL,"
            " return_date DATE,"
            " FOREIGN KEY (book_id) REFERENCES books(id) ON DELETE CASCADE,"
            " FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE"
            ") ENGINE=InnoDB"
        )
        for name, ddl in tables.items():
            self.cursor.execute(ddl)
        self.conn.commit()

    def execute(self, query, params=None, commit=False, fetch=False):
        try:
            self.cursor.execute(query, params or ())
            if commit:
                self.conn.commit()
            if fetch:
                return self.cursor.fetchall()
            return None
        except mysql.connector.Error as err:
            raise

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

# ---------------------- GUI Application ----------------------
class LibraryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Library Management System - Connect to Database")
        self.db = DB()
        self._build_connect_window()

    def _build_connect_window(self):
        frm = ttk.Frame(self.root, padding=12)
        frm.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frm, text="MySQL Host:").grid(row=0, column=0, sticky=tk.W, pady=4)
        ttk.Label(frm, text="User:").grid(row=1, column=0, sticky=tk.W, pady=4)
        ttk.Label(frm, text="Password:").grid(row=2, column=0, sticky=tk.W, pady=4)
        ttk.Label(frm, text="Database name:").grid(row=3, column=0, sticky=tk.W, pady=4)

        self.host_var = tk.StringVar(value="localhost")
        self.user_var = tk.StringVar(value="root")
        self.pass_var = tk.StringVar(value="Sandeep778")
        self.dbname_var = tk.StringVar(value="library_db")

        ttk.Entry(frm, textvariable=self.host_var).grid(row=0, column=1, pady=4)
        ttk.Entry(frm, textvariable=self.user_var).grid(row=1, column=1, pady=4)
        ttk.Entry(frm, textvariable=self.pass_var, show="*").grid(row=2, column=1, pady=4)
        ttk.Entry(frm, textvariable=self.dbname_var).grid(row=3, column=1, pady=4)

        btn = ttk.Button(frm, text="Connect", command=self._attempt_connect)
        btn.grid(row=4, column=0, columnspan=2, pady=10)

    def _attempt_connect(self):
        host = self.host_var.get().strip()
        user = self.user_var.get().strip()
        pwd = self.pass_var.get()
        dbname = self.dbname_var.get().strip() or "library_db"

        ok, msg = self.db.connect(host, user, pwd, dbname)
        if not ok:
            messagebox.showerror("Connection failed", msg)
            return
        messagebox.showinfo("Success", msg)
        # destroy connect UI and open main app
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title("Library Management System")
        self._build_main_ui()

    # ---------------------- Main UI ----------------------
    def _build_main_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tabs
        self.tab_books = ttk.Frame(self.notebook)
        self.tab_students = ttk.Frame(self.notebook)
        self.tab_issue = ttk.Frame(self.notebook)
        self.tab_search = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_books, text="Books")
        self.notebook.add(self.tab_students, text="Students")
        self.notebook.add(self.tab_issue, text="Issue / Return")
        self.notebook.add(self.tab_search, text="Search")
        self.notebook.add(self.tab_reports, text="Reports")

        self._build_books_tab()
        self._build_students_tab()
        self._build_issue_tab()
        self._build_search_tab()
        self._build_reports_tab()

    # ---------------------- Books Tab ----------------------
    def _build_books_tab(self):
        frm = ttk.Frame(self.tab_books, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        # Form
        labels = ["Title", "Author", "Year", "ISBN", "Copies"]
        self.book_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar(value="1")]
        for i, lbl in enumerate(labels):
            ttk.Label(frm, text=lbl+":").grid(row=i, column=0, sticky=tk.W, pady=2)
            ttk.Entry(frm, textvariable=self.book_vars[i]).grid(row=i, column=1, pady=2, sticky=tk.EW)
        ttk.Button(frm, text="Add / Update Book", command=self.add_or_update_book).grid(row=5, column=0, pady=6)
        ttk.Button(frm, text="Clear Fields", command=self.clear_book_fields).grid(row=5, column=1, pady=6)

        # Book list
        self.books_tree = ttk.Treeview(frm, columns=("id","title","author","year","isbn","copies"), show="headings", height=10)
        for col, hd in zip(("id","title","author","year","isbn","copies"), ("ID","Title","Author","Year","ISBN","Copies")):
            self.books_tree.heading(col, text=hd)
            self.books_tree.column(col, width=80 if col=="id" else 140)
        self.books_tree.grid(row=6, column=0, columnspan=2, sticky=tk.NSEW)
        frm.rowconfigure(6, weight=1)
        self.books_tree.bind("<Double-1>", self.on_book_select)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=7, column=0, columnspan=2, pady=6)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected_book).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Refresh List", command=self.refresh_books).grid(row=0, column=1, padx=6)

        self.refresh_books()

    def clear_book_fields(self):
        for v in self.book_vars:
            v.set("")

    def add_or_update_book(self):
        title = self.book_vars[0].get().strip()
        author = self.book_vars[1].get().strip()
        year = self.book_vars[2].get().strip()
        isbn = self.book_vars[3].get().strip()
        copies = self.book_vars[4].get().strip() or "1"

        if not title:
            messagebox.showwarning("Validation", "Title chahiye.")
            return
        try:
            year_val = int(year) if year else None
            copies_val = int(copies)
        except ValueError:
            messagebox.showwarning("Validation", "Year/Copies integer hone chahiye.")
            return

        # Try insert; if ISBN exists then update copies and other fields
        try:
            # check exists by ISBN
            rows = self.db.execute("SELECT id FROM books WHERE isbn = %s", (isbn,), fetch=True)
            if rows:
                book_id = rows[0][0]
                self.db.execute(
                    "UPDATE books SET title=%s, author=%s, year=%s, copies=%s WHERE id=%s",
                    (title, author, year_val, copies_val, book_id), commit=True
                )
                messagebox.showinfo("Updated", "Book updated.")
            else:
                self.db.execute(
                    "INSERT INTO books (title, author, year, isbn, copies) VALUES (%s,%s,%s,%s,%s)",
                    (title, author, year_val, isbn, copies_val), commit=True
                )
                messagebox.showinfo("Added", "Book added.")
            self.refresh_books()
            self.clear_book_fields()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def refresh_books(self):
        for i in self.books_tree.get_children():
            self.books_tree.delete(i)
        try:
            rows = self.db.execute("SELECT id,title,author,year,isbn,copies FROM books", fetch=True)
            for r in rows:
                self.books_tree.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_book_select(self, event):
        sel = self.books_tree.selection()
        if not sel:
            return
        vals = self.books_tree.item(sel[0], "values")
        # fill fields
        self.book_vars[0].set(vals[1])
        self.book_vars[1].set(vals[2])
        self.book_vars[2].set(vals[3])
        self.book_vars[3].set(vals[4])
        self.book_vars[4].set(vals[5])

    def delete_selected_book(self):
        sel = self.books_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Book select karo.")
            return
        vals = self.books_tree.item(sel[0], "values")
        book_id = vals[0]
        if messagebox.askyesno("Confirm", f"Delete book '{vals[1]}'?"):
            try:
                self.db.execute("DELETE FROM books WHERE id=%s", (book_id,), commit=True)
                self.refresh_books()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

    # ---------------------- Students Tab ----------------------
    def _build_students_tab(self):
        frm = ttk.Frame(self.tab_students, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        labels = ["Name", "Roll", "Email", "Phone"]
        self.stu_vars = [tk.StringVar(), tk.StringVar(), tk.StringVar(), tk.StringVar()]
        for i, lbl in enumerate(labels):
            ttk.Label(frm, text=lbl+":").grid(row=i, column=0, sticky=tk.W, pady=2)
            ttk.Entry(frm, textvariable=self.stu_vars[i]).grid(row=i, column=1, pady=2, sticky=tk.EW)
        ttk.Button(frm, text="Register / Update Student", command=self.add_or_update_student).grid(row=4, column=0, pady=6)
        ttk.Button(frm, text="Clear", command=lambda: [v.set("") for v in self.stu_vars]).grid(row=4, column=1, pady=6)

        self.students_tree = ttk.Treeview(frm, columns=("id","name","roll","email","phone"), show="headings", height=10)
        for col, hd in zip(("id","name","roll","email","phone"), ("ID","Name","Roll","Email","Phone")):
            self.students_tree.heading(col, text=hd)
            self.students_tree.column(col, width=100 if col=="id" else 160)
        self.students_tree.grid(row=5, column=0, columnspan=2, sticky=tk.NSEW)
        frm.rowconfigure(5, weight=1)
        self.students_tree.bind("<Double-1>", self.on_student_select)

        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=6, column=0, columnspan=2, pady=6)
        ttk.Button(btn_frame, text="Delete Selected", command=self.delete_selected_student).grid(row=0, column=0, padx=6)
        ttk.Button(btn_frame, text="Refresh List", command=self.refresh_students).grid(row=0, column=1, padx=6)

        self.refresh_students()

    def add_or_update_student(self):
        name = self.stu_vars[0].get().strip()
        roll = self.stu_vars[1].get().strip()
        email = self.stu_vars[2].get().strip()
        phone = self.stu_vars[3].get().strip()
        if not name:
            messagebox.showwarning("Validation", "Naam chahiye.")
            return
        try:
            rows = self.db.execute("SELECT id FROM students WHERE roll=%s", (roll,), fetch=True) if roll else []
            if rows:
                sid = rows[0][0]
                self.db.execute("UPDATE students SET name=%s,email=%s,phone=%s WHERE id=%s", (name,email,phone,sid), commit=True)
                messagebox.showinfo("Updated", "Student updated.")
            else:
                self.db.execute("INSERT INTO students (name,roll,email,phone) VALUES (%s,%s,%s,%s)", (name,roll,email,phone), commit=True)
                messagebox.showinfo("Registered", "Student registered.")
            self.refresh_students()
            for v in self.stu_vars: v.set("")
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def refresh_students(self):
        for i in self.students_tree.get_children():
            self.students_tree.delete(i)
        try:
            rows = self.db.execute("SELECT id,name,roll,email,phone FROM students", fetch=True)
            for r in rows:
                self.students_tree.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def on_student_select(self, event):
        sel = self.students_tree.selection()
        if not sel:
            return
        vals = self.students_tree.item(sel[0], "values")
        self.stu_vars[0].set(vals[1])
        self.stu_vars[1].set(vals[2])
        self.stu_vars[2].set(vals[3])
        self.stu_vars[3].set(vals[4])

    def delete_selected_student(self):
        sel = self.students_tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Student select karo.")
            return
        vals = self.students_tree.item(sel[0], "values")
        sid = vals[0]
        if messagebox.askyesno("Confirm", f"Delete student '{vals[1]}'? This also removes any issues tied to them."):
            try:
                self.db.execute("DELETE FROM students WHERE id=%s", (sid,), commit=True)
                self.refresh_students()
            except Exception as e:
                messagebox.showerror("DB Error", str(e))

    # ---------------------- Issue / Return Tab ----------------------
    def _build_issue_tab(self):
        frm = ttk.Frame(self.tab_issue, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)

        # Issue book
        issue_frame = ttk.LabelFrame(frm, text="Issue Book", padding=8)
        issue_frame.grid(row=0, column=0, sticky=tk.NSEW, padx=6, pady=6)

        ttk.Label(issue_frame, text="Book ID or ISBN:").grid(row=0, column=0, sticky=tk.W)
        ttk.Label(issue_frame, text="Student Roll or ID:").grid(row=1, column=0, sticky=tk.W)
        self.issue_book_var = tk.StringVar()
        self.issue_student_var = tk.StringVar()
        ttk.Entry(issue_frame, textvariable=self.issue_book_var).grid(row=0, column=1, pady=4)
        ttk.Entry(issue_frame, textvariable=self.issue_student_var).grid(row=1, column=1, pady=4)
        ttk.Label(issue_frame, text="Days (due):").grid(row=2, column=0, sticky=tk.W)
        self.issue_days_var = tk.StringVar(value="14")
        ttk.Entry(issue_frame, textvariable=self.issue_days_var).grid(row=2, column=1, pady=4)
        ttk.Button(issue_frame, text="Issue", command=self.issue_book).grid(row=3, column=0, columnspan=2, pady=6)

        # Return book
        return_frame = ttk.LabelFrame(frm, text="Return Book", padding=8)
        return_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=6, pady=6)

        ttk.Label(return_frame, text="Issue ID:").grid(row=0, column=0, sticky=tk.W)
        self.return_issue_var = tk.StringVar()
        ttk.Entry(return_frame, textvariable=self.return_issue_var).grid(row=0, column=1, pady=4)
        ttk.Button(return_frame, text="Return", command=self.return_book).grid(row=1, column=0, columnspan=2, pady=6)

        # Active issues listing
        self.issues_tree = ttk.Treeview(frm, columns=("id","book_title","student_name","issue_date","due_date","return_date"), show="headings", height=10)
        for col, hd in zip(("id","book_title","student_name","issue_date","due_date","return_date"),
                           ("IssueID","Book","Student","IssueDate","DueDate","ReturnDate")):
            self.issues_tree.heading(col, text=hd)
            self.issues_tree.column(col, width=120)
        self.issues_tree.grid(row=1, column=0, columnspan=2, sticky=tk.NSEW, pady=8)
        frm.rowconfigure(1, weight=1)
        ttk.Button(frm, text="Refresh Issues", command=self.refresh_issues).grid(row=2, column=0, columnspan=2, pady=6)
        self.refresh_issues()

    def _resolve_book_id(self, book_identifier):
        # accepts numeric id or ISBN or title
        if not book_identifier:
            return None
        book_identifier = book_identifier.strip()
        # try numeric id
        try:
            bid = int(book_identifier)
            rows = self.db.execute("SELECT id,copies FROM books WHERE id=%s", (bid,), fetch=True)
            if rows:
                return rows[0][0], rows[0][1]
        except ValueError:
            pass
        # try isbn
        rows = self.db.execute("SELECT id,copies FROM books WHERE isbn=%s", (book_identifier,), fetch=True)
        if rows:
            return rows[0][0], rows[0][1]
        # try title
        rows = self.db.execute("SELECT id,copies FROM books WHERE title LIKE %s", (f"%{book_identifier}%",), fetch=True)
        if rows:
            return rows[0][0], rows[0][1]
        return None

    def _resolve_student_id(self, student_identifier):
        if not student_identifier:
            return None
        student_identifier = student_identifier.strip()
        # try numeric id
        try:
            sid = int(student_identifier)
            rows = self.db.execute("SELECT id FROM students WHERE id=%s", (sid,), fetch=True)
            if rows:
                return rows[0][0]
        except ValueError:
            pass
        # try roll
        rows = self.db.execute("SELECT id FROM students WHERE roll=%s", (student_identifier,), fetch=True)
        if rows:
            return rows[0][0]
        # try name search
        rows = self.db.execute("SELECT id FROM students WHERE name LIKE %s", (f"%{student_identifier}%",), fetch=True)
        if rows:
            return rows[0][0]
        return None

    def issue_book(self):
        bookid_info = self._resolve_book_id(self.issue_book_var.get())
        student_id = self._resolve_student_id(self.issue_student_var.get())
        if not bookid_info:
            messagebox.showwarning("Not found", "Book not found.")
            return
        if not student_id:
            messagebox.showwarning("Not found", "Student not found.")
            return
        book_id, copies = bookid_info
        if copies <= 0:
            messagebox.showwarning("Unavailable", "Books not available (copies=0).")
            return
        try:
            days = int(self.issue_days_var.get())
        except ValueError:
            days = 14
        issue_date = datetime.now().date()
        due_date = issue_date + timedelta(days=days)
        try:
            self.db.execute("INSERT INTO issues (book_id, student_id, issue_date, due_date) VALUES (%s,%s,%s,%s)",
                            (book_id, student_id, issue_date, due_date), commit=True)
            # decrement copies
            self.db.execute("UPDATE books SET copies = copies - 1 WHERE id=%s", (book_id,), commit=True)
            messagebox.showinfo("Issued", f"Book issued. Due: {due_date.isoformat()}")
            self.issue_book_var.set("")
            self.issue_student_var.set("")
            self.refresh_books()
            self.refresh_issues()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def refresh_issues(self):
        for i in self.issues_tree.get_children():
            self.issues_tree.delete(i)
        try:
            rows = self.db.execute(
                "SELECT i.id, b.title, s.name, i.issue_date, i.due_date, i.return_date "
                "FROM issues i JOIN books b ON i.book_id=b.id JOIN students s ON i.student_id=s.id "
                "ORDER BY i.issue_date DESC", fetch=True)
            for r in rows:
                self.issues_tree.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def return_book(self):
        issue_id_raw = self.return_issue_var.get().strip()
        if not issue_id_raw:
            messagebox.showwarning("Input", "Issue ID do.")
            return
        try:
            issue_id = int(issue_id_raw)
        except ValueError:
            messagebox.showwarning("Input", "Issue ID numeric hona chahiye.")
            return
        try:
            rows = self.db.execute("SELECT book_id, issue_date, due_date, return_date FROM issues WHERE id=%s", (issue_id,), fetch=True)
            if not rows:
                messagebox.showwarning("Not found", "Issue record nahi mila.")
                return
            book_id, issue_date, due_date, return_date = rows[0]
            if return_date is not None:
                messagebox.showinfo("Already returned", "Yeh book pehle hi return ho chuki hai.")
                return
            today = datetime.now().date()
            self.db.execute("UPDATE issues SET return_date=%s WHERE id=%s", (today, issue_id), commit=True)
            # increment copies
            self.db.execute("UPDATE books SET copies = copies + 1 WHERE id=%s", (book_id,), commit=True)
            # fine calculation (simple):  default fine 5 per day late
            fine = 0
            if today > due_date:
                days_late = (today - due_date).days
                fine = days_late * 5
            msg = "Book returned."
            if fine:
                msg += f" Late by {days_late} days. Fine = {fine}."
            messagebox.showinfo("Returned", msg)
            self.return_issue_var.set("")
            self.refresh_books()
            self.refresh_issues()
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    # ---------------------- Search Tab ----------------------
    def _build_search_tab(self):
        frm = ttk.Frame(self.tab_search, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Label(frm, text="Search books by title/author/isbn:").grid(row=0, column=0, sticky=tk.W)
        self.search_var = tk.StringVar()
        ttk.Entry(frm, textvariable=self.search_var).grid(row=0, column=1, sticky=tk.EW, pady=4)
        ttk.Button(frm, text="Search", command=self.search_books).grid(row=0, column=2, padx=6)
        self.search_tree = ttk.Treeview(frm, columns=("id","title","author","year","isbn","copies"), show="headings", height=12)
        for col, hd in zip(("id","title","author","year","isbn","copies"), ("ID","Title","Author","Year","ISBN","Copies")):
            self.search_tree.heading(col, text=hd)
        self.search_tree.grid(row=1, column=0, columnspan=3, sticky=tk.NSEW)
        frm.rowconfigure(1, weight=1)
        ttk.Button(frm, text="Refresh All Books", command=self.refresh_books_in_search).grid(row=2, column=0, pady=6)
        self.refresh_books_in_search()

    def search_books(self):
        term = self.search_var.get().strip()
        if not term:
            self.refresh_books_in_search()
            return
        try:
            rows = self.db.execute("SELECT id,title,author,year,isbn,copies FROM books WHERE title LIKE %s OR author LIKE %s OR isbn LIKE %s",
                                   (f"%{term}%", f"%{term}%", f"%{term}%"), fetch=True)
            for i in self.search_tree.get_children():
                self.search_tree.delete(i)
            for r in rows:
                self.search_tree.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def refresh_books_in_search(self):
        try:
            rows = self.db.execute("SELECT id,title,author,year,isbn,copies FROM books", fetch=True)
            for i in self.search_tree.get_children():
                self.search_tree.delete(i)
            for r in rows:
                self.search_tree.insert("", tk.END, values=r)
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    # ---------------------- Reports Tab ----------------------
    def _build_reports_tab(self):
        frm = ttk.Frame(self.tab_reports, padding=8)
        frm.pack(fill=tk.BOTH, expand=True)
        ttk.Button(frm, text="Currently Issued Books", command=self.report_issued).pack(fill=tk.X, pady=6)
        ttk.Button(frm, text="Overdue Books", command=self.report_overdue).pack(fill=tk.X, pady=6)
        ttk.Button(frm, text="Students with books", command=self.report_students_with_books).pack(fill=tk.X, pady=6)
        self.report_text = tk.Text(frm, height=20)
        self.report_text.pack(fill=tk.BOTH, expand=True, pady=6)

    def report_issued(self):
        try:
            rows = self.db.execute(
                "SELECT i.id, b.title, s.name, i.issue_date, i.due_date "
                "FROM issues i JOIN books b ON i.book_id=b.id JOIN students s ON i.student_id=s.id "
                "WHERE i.return_date IS NULL ORDER BY i.due_date ASC", fetch=True)
            self._show_report("Currently Issued Books", rows, ["IssueID","Book","Student","IssueDate","DueDate"])
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def report_overdue(self):
        try:
            today = datetime.now().date()
            rows = self.db.execute(
                "SELECT i.id, b.title, s.name, i.issue_date, i.due_date, DATEDIFF(%s, i.due_date) as days_late "
                "FROM issues i JOIN books b ON i.book_id=b.id JOIN students s ON i.student_id=s.id "
                "WHERE i.return_date IS NULL AND i.due_date < %s ORDER BY days_late DESC", (today, today), fetch=True)
            self._show_report("Overdue Books", rows, ["IssueID","Book","Student","IssueDate","DueDate","DaysLate"])
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def report_students_with_books(self):
        try:
            rows = self.db.execute(
                "SELECT s.id, s.name, s.roll, COUNT(i.id) as books_count "
                "FROM students s LEFT JOIN issues i ON s.id=i.student_id AND i.return_date IS NULL "
                "GROUP BY s.id HAVING books_count>0", fetch=True)
            self._show_report("Students with books", rows, ["StudentID","Name","Roll","BooksCount"])
        except Exception as e:
            messagebox.showerror("DB Error", str(e))

    def _show_report(self, title, rows, headers):
        self.report_text.delete("1.0", tk.END)
        self.report_text.insert(tk.END, title + "\n" + "="*len(title) + "\n\n")
        if not rows:
            self.report_text.insert(tk.END, "No records.\n")
            return
        # show header
        self.report_text.insert(tk.END, "\t".join(headers) + "\n")
        self.report_text.insert(tk.END, "-"*60 + "\n")
        for r in rows:
            self.report_text.insert(tk.END, "\t".join(str(x) for x in r) + "\n")

# ---------------------- Run ----------------------
def main():
    root = tk.Tk()
    root.geometry("900x600")
    app = LibraryApp(root)
    root.mainloop()
    # on close
    try:
        app.db.close()
    except:
        pass

if __name__ == "__main__":
    main()
