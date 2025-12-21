import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import csv

# -----------------------------
# DSA Core: Hash Table + Merge Sort
# -----------------------------

class Book:
    def __init__(self, isbn, title, author, year):
        self.isbn = isbn
        self.title = title
        self.author = author
        self.year = year

class HashTable:
    def __init__(self, size=20):
        self.size = size
        self.table = [[] for _ in range(size)]

    def hash_function(self, isbn):
        return sum(ord(c) for c in isbn) % self.size

    def insert(self, book):
        index = self.hash_function(book.isbn)
        for b in self.table[index]:
            if b.isbn == book.isbn:
                return False  # duplicate
        self.table[index].append(book)
        return True

    def search(self, isbn):
        index = self.hash_function(isbn)
        for book in self.table[index]:
            if book.isbn == isbn:
                return book
        return None

    def delete(self, isbn):
        index = self.hash_function(isbn)
        for book in self.table[index]:
            if book.isbn == isbn:
                self.table[index].remove(book)
                return True
        return False

    def update(self, isbn, title, author, year):
        book = self.search(isbn)
        if book:
            book.title = title
            book.author = author
            book.year = year
            return True
        return False

    def get_all_books(self):
        books = []
        for chain in self.table:
            books.extend(chain)
        return books

# Merge sort (by title)
def merge_sort(books):
    if len(books) <= 1:
        return books
    mid = len(books) // 2
    left = merge_sort(books[:mid])
    right = merge_sort(books[mid:])
    return merge(left, right)

def merge(left, right):
    result = []
    i = j = 0
    while i < len(left) and j < len(right):
        if left[i].title.lower() < right[j].title.lower():
            result.append(left[i])
            i += 1
        else:
            result.append(right[j])
            j += 1
    result.extend(left[i:])
    result.extend(right[j:])
    return result

# -----------------------------
# Main Application GUI
# -----------------------------

hash_table = HashTable()

root = tk.Tk()
root.title("Library Management System (DSA Based)")
root.geometry("1080x650")
root.config(bg="#ececec")

# -----------------------------
# Top Frame (Title + Clock)
# -----------------------------
def update_time():
    current_time = time.strftime("%H:%M:%S")
    clock_label.config(text=current_time)
    root.after(1000, update_time)

title_frame = tk.Frame(root, bg="#3c3f41")
title_frame.pack(fill="x")

title_label = tk.Label(title_frame, text="Library Management System (DSA - Hashing + Sorting)",
                       font=("Arial", 20, "bold"), bg="#3c3f41", fg="white", pady=10)
title_label.pack(side="left", padx=20)

clock_label = tk.Label(title_frame, font=("Arial", 14), bg="#3c3f41", fg="white")
clock_label.pack(side="right", padx=20)
update_time()

# -----------------------------
# Left Frame (Buttons)
# -----------------------------
left_frame = tk.Frame(root, bg="#2f3136", width=250)
left_frame.pack(side="left", fill="y")

def open_add_window():
    win = tk.Toplevel(root)
    win.title("Add Book")
    win.geometry("400x300")

    tk.Label(win, text="ISBN:").pack(pady=5)
    isbn_entry = tk.Entry(win, width=40)
    isbn_entry.pack()

    tk.Label(win, text="Title:").pack(pady=5)
    title_entry = tk.Entry(win, width=40)
    title_entry.pack()

    tk.Label(win, text="Author:").pack(pady=5)
    author_entry = tk.Entry(win, width=40)
    author_entry.pack()

    tk.Label(win, text="Year:").pack(pady=5)
    year_entry = tk.Entry(win, width=40)
    year_entry.pack()

    def add_book_action():
        isbn = isbn_entry.get().strip()
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        year = year_entry.get().strip()

        if not isbn or not title or not author or not year:
            messagebox.showwarning("Warning", "All fields are required.")
            return
        try:
            year = int(year)
        except:
            messagebox.showerror("Error", "Year must be a number.")
            return

        book = Book(isbn, title, author, year)
        if hash_table.insert(book):
            messagebox.showinfo("Success", "Book added successfully.")
            win.destroy()
            display_books()
        else:
            messagebox.showerror("Error", "Book with this ISBN already exists.")

    tk.Button(win, text="Add Book", bg="#5cb85c", fg="white", command=add_book_action).pack(pady=15)

def open_search_window():
    win = tk.Toplevel(root)
    win.title("Search Book")
    win.geometry("400x200")

    tk.Label(win, text="Enter ISBN:").pack(pady=5)
    isbn_entry = tk.Entry(win, width=40)
    isbn_entry.pack()

    def search_action():
        isbn = isbn_entry.get().strip()
        if not isbn:
            messagebox.showwarning("Warning", "Enter ISBN to search.")
            return
        book = hash_table.search(isbn)
        if book:
            messagebox.showinfo("Book Found",
                                f"ISBN: {book.isbn}\nTitle: {book.title}\nAuthor: {book.author}\nYear: {book.year}")
        else:
            messagebox.showerror("Not Found", "Book not found.")

    tk.Button(win, text="Search", bg="#0275d8", fg="white", command=search_action).pack(pady=10)
def open_update_window():
    win = tk.Toplevel(root)
    win.title("Update Book")
    win.geometry("400x350")

    tk.Label(win, text="Enter ISBN to Update:").pack(pady=5)
    isbn_entry = tk.Entry(win, width=40)
    isbn_entry.pack()

    # Frame for editable fields
    tk.Label(win, text="Title:").pack(pady=5)
    title_entry = tk.Entry(win, width=40)
    title_entry.pack()

    tk.Label(win, text="Author:").pack(pady=5)
    author_entry = tk.Entry(win, width=40)
    author_entry.pack()

    tk.Label(win, text="Year:").pack(pady=5)
    year_entry = tk.Entry(win, width=40)
    year_entry.pack()

    # Function to fetch current book details
    def load_book_data():
        isbn = isbn_entry.get().strip()
        if not isbn:
            messagebox.showwarning("Warning", "Enter ISBN to load details.")
            return

        book = hash_table.search(isbn)
        if book:
            # Clear existing entries
            title_entry.delete(0, tk.END)
            author_entry.delete(0, tk.END)
            year_entry.delete(0, tk.END)
            # Insert current values
            title_entry.insert(0, book.title)
            author_entry.insert(0, book.author)
            year_entry.insert(0, book.year)
        else:
            messagebox.showerror("Error", "Book not found.")

    tk.Button(win, text="Load Book Data", bg="#0275d8", fg="white",
              command=load_book_data).pack(pady=10)

    def update_action():
        isbn = isbn_entry.get().strip()
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        year = year_entry.get().strip()

        if not isbn or not title or not author or not year:
            messagebox.showwarning("Warning", "All fields are required.")
            return

        try:
            year = int(year)
        except:
            messagebox.showerror("Error", "Year must be a number.")
            return

        if hash_table.update(isbn, title, author, year):
            messagebox.showinfo("Success", "Book updated successfully.")
            win.destroy()
            display_books()
        else:
            messagebox.showerror("Error", "Book not found.")

    tk.Button(win, text="Update Book", bg="#f0ad4e", fg="white",
              command=update_action).pack(pady=10)

def open_delete_window():
    win = tk.Toplevel(root)
    win.title("Delete Book")
    win.geometry("350x200")

    tk.Label(win, text="Enter ISBN to Delete:").pack(pady=5)
    isbn_entry = tk.Entry(win, width=40)
    isbn_entry.pack()

    def delete_action():
        isbn = isbn_entry.get().strip()
        if not isbn:
            messagebox.showwarning("Warning", "Enter ISBN to delete.")
            return

        if hash_table.delete(isbn):
            messagebox.showinfo("Success", "Book deleted successfully.")
            win.destroy()
            display_books()
        else:
            messagebox.showerror("Error", "Book not found.")

    tk.Button(win, text="Delete Book", bg="#d9534f", fg="white", command=delete_action).pack(pady=10)

def display_books():
    for row in book_table.get_children():
        book_table.delete(row)
    all_books = hash_table.get_all_books()
    sorted_books = merge_sort(all_books)
    for b in sorted_books:
        book_table.insert("", tk.END, values=(b.isbn, b.title, b.author, b.year))

def export_data():
    books = hash_table.get_all_books()
    if not books:
        messagebox.showerror("Error", "No data to export.")
        return

    file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if not file_path:
        return

    with open(file_path, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["ISBN", "Title", "Author", "Year"])
        for book in books:
            writer.writerow([book.isbn, book.title, book.author, book.year])
    messagebox.showinfo("Success", "Data exported successfully!")

# Left-side buttons
buttons = [
    ("Add Book", open_add_window, "#5cb85c"),
    ("Update Book", open_update_window, "#f0ad4e"),
    ("Delete Book", open_delete_window, "#d9534f"),
    ("Search Book", open_search_window, "#0275d8"),
    ("Show All", display_books, "#764ef0"),
    ("Export Data", export_data, "#17a2b8"),
    ("Exit", root.destroy, "#6c757d")
]

for text, cmd, color in buttons:
    tk.Button(left_frame, text=text, command=cmd, bg=color, fg="white",
              font=("Arial", 12, "bold"), width=20, height=2).pack(pady=10)

# -----------------------------
# Right Frame (Table)
# -----------------------------
right_frame = tk.Frame(root, bg="white")
right_frame.pack(side="right", fill="both", expand=True)

cols = ("ISBN", "Title", "Author", "Year")
book_table = ttk.Treeview(right_frame, columns=cols, show="headings")
for col in cols:
    book_table.heading(col, text=col)
    book_table.column(col, width=180, anchor='center')
book_table.pack(fill="both", expand=True, padx=10, pady=10)

root.mainloop()
