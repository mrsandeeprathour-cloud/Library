from tkinter import *
from tkinter import ttk, messagebox, filedialog
import ttkthemes
import pymysql
import time
from datetime import datetime
import csv

# ========================== Database ==========================
def connect_database():
    def connect():
        global mycursor, con
        try:
            con = pymysql.connect(
                host=hostEntry.get(),
                user=userEntry.get(),
                password=passwordEntry.get()
            )
            mycursor = con.cursor()
            mycursor.execute("CREATE DATABASE IF NOT EXISTS librarymanagementsystem")
            mycursor.execute("USE librarymanagementsystem")
            mycursor.execute("""
                CREATE TABLE IF NOT EXISTS books (
                    ISBN VARCHAR(50) PRIMARY KEY,
                    Title VARCHAR(255) NOT NULL,
                    Author VARCHAR(255),
                    Year INT,
                    Added_Date DATE,
                    Added_Time TIME
                )
            """)
            con.commit()
            messagebox.showinfo('Success', 'Database Connected and Created Successfully', parent=connectWindow)
            enable_buttons()
            connectWindow.destroy()
        except pymysql.err.OperationalError as e:
            messagebox.showerror('Error', f'Connection failed: {e}', parent=connectWindow)
            passwordEntry.delete(0, END)
        except Exception as e:
            passwordEntry.delete(0, END)
            messagebox.showerror('Error', f'Connection failed: {e}', parent=connectWindow)

    connectWindow = Toplevel()
    connectWindow.grab_set()
    connectWindow.geometry('470x250+730+230')
    connectWindow.title('Connect Database')
    connectWindow.resizable(False, False)

    Label(connectWindow, text='Host Name', font=('times new roman', 18, 'bold')).grid(row=0, column=0, padx=20, pady=8)
    hostEntry = Entry(connectWindow, font=('times new roman', 14, 'bold'), bd=2)
    hostEntry.grid(row=0, column=1, padx=20, pady=8)
    hostEntry.insert(0, 'localhost')

    Label(connectWindow, text='User Name', font=('times new roman', 18, 'bold')).grid(row=1, column=0, padx=20, pady=8)
    userEntry = Entry(connectWindow, font=('times new roman', 14, 'bold'), bd=2)
    userEntry.grid(row=1, column=1, padx=20, pady=8)
    userEntry.insert(0, 'root')

    Label(connectWindow, text='Password', font=('times new roman', 18, 'bold')).grid(row=2, column=0, padx=20, pady=8)
    passwordEntry = Entry(connectWindow, font=('times new roman', 14, 'bold'), bd=2, show='*')
    passwordEntry.grid(row=2, column=1, padx=20, pady=8)

    ttk.Button(connectWindow, text='Connect', cursor='hand2', command=connect).grid(row=3, columnspan=2, pady=12)


def enable_buttons():
    for btn in [addBookButton, searchBookButton, updateBookButton,
                deleteBookButton, showBookButton, exportBookButton]:
        btn.config(state=NORMAL)

# ========================== Book Operations ==========================
def check_connection():
    if 'mycursor' not in globals():
        messagebox.showerror('Error', 'Database not connected')
        return False
    return True

def show_books():
    if not check_connection(): return
    try:
        mycursor.execute('SELECT * FROM books')
        data = mycursor.fetchall()
        bookTable.delete(*bookTable.get_children())
        for row in data:
            bookTable.insert('', END, values=row)
    except Exception as e:
        messagebox.showerror('Error', f'Unable to fetch data: {e}')

def add_book():
    if not check_connection(): return

    def add_data():
        isbn = isbn_entry.get().strip()
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        year_txt = year_entry.get().strip()

        if not isbn or not title:
            messagebox.showerror('Error', 'ISBN and Title are required', parent=add_window)
            return

        try:
            year = int(year_txt) if year_txt else None
        except ValueError:
            messagebox.showerror('Error', 'Year must be a number', parent=add_window)
            return

        try:
            query = 'INSERT INTO books (ISBN, Title, Author, Year, Added_Date, Added_Time) VALUES (%s,%s,%s,%s,%s,%s)'
            mycursor.execute(query, (
                isbn, title, author if author else None, year,
                time.strftime("%Y-%m-%d"), time.strftime("%H:%M:%S")
            ))
            con.commit()
            messagebox.showinfo('Success', 'Book Added Successfully', parent=add_window)
            add_window.destroy()
            show_books()
        except pymysql.err.IntegrityError:
            messagebox.showerror('Error', 'ISBN already exists', parent=add_window)
        except Exception as e:
            messagebox.showerror('Error', f'{e}', parent=add_window)

    add_window = Toplevel()
    add_window.title('Add Book')
    add_window.geometry('400x350')
    add_window.grab_set()

    Label(add_window, text='ISBN').pack(pady=6)
    isbn_entry = Entry(add_window)
    isbn_entry.pack(pady=6)

    Label(add_window, text='Title').pack(pady=6)
    title_entry = Entry(add_window)
    title_entry.pack(pady=6)

    Label(add_window, text='Author').pack(pady=6)
    author_entry = Entry(add_window)
    author_entry.pack(pady=6)

    Label(add_window, text='Year (optional)').pack(pady=6)
    year_entry = Entry(add_window)
    year_entry.pack(pady=6)

    ttk.Button(add_window, text='Add Book', command=add_data).pack(pady=12)

def delete_book():
    if not check_connection(): return
    selected_item = bookTable.focus()
    if not selected_item:
        messagebox.showerror('Error', 'Please select a book to delete')
        return

    isbn = bookTable.item(selected_item)['values'][0]
    if messagebox.askyesno('Confirm Delete', f'Do you really want to delete ISBN {isbn}?'):
        try:
            mycursor.execute('DELETE FROM books WHERE ISBN=%s', (isbn,))
            con.commit()
            bookTable.delete(selected_item)
            messagebox.showinfo('Deleted', f'Book ISBN {isbn} deleted successfully')
        except Exception as e:
            messagebox.showerror('Error', f'Error deleting record: {e}')

def update_book():
    if not check_connection(): return
    selected = bookTable.focus()
    if not selected:
        messagebox.showerror('Error', 'Select a book')
        return

    data = bookTable.item(selected)['values']

    def save_update():
        title = title_entry.get().strip()
        author = author_entry.get().strip()
        year_txt = year_entry.get().strip()

        if not title:
            messagebox.showerror('Error', 'Title is required', parent=update_window)
            return
        try:
            year = int(year_txt) if year_txt else None
        except ValueError:
            messagebox.showerror('Error', 'Year must be a number', parent=update_window)
            return

        try:
            query = "UPDATE books SET Title=%s, Author=%s, Year=%s WHERE ISBN=%s"
            mycursor.execute(query, (title, author if author else None, year, data[0]))
            con.commit()
            messagebox.showinfo('Success', 'Book details updated successfully', parent=update_window)
            update_window.destroy()
            show_books()
        except Exception as e:
            messagebox.showerror('Error', f'Update failed: {e}', parent=update_window)

    update_window = Toplevel()
    update_window.title('Update Book')
    update_window.geometry('400x350')
    update_window.grab_set()

    Label(update_window, text='ISBN').pack(pady=6)
    isbn_entry = Entry(update_window)
    isbn_entry.pack(pady=6)
    isbn_entry.insert(0, data[0])
    isbn_entry.config(state='readonly')

    Label(update_window, text='Title').pack(pady=6)
    title_entry = Entry(update_window)
    title_entry.pack(pady=6)
    title_entry.insert(0, data[1])

    Label(update_window, text='Author').pack(pady=6)
    author_entry = Entry(update_window)
    author_entry.pack(pady=6)
    author_entry.insert(0, data[2] if data[2] is not None else '')

    Label(update_window, text='Year (optional)').pack(pady=6)
    year_entry = Entry(update_window)
    year_entry.pack(pady=6)
    year_entry.insert(0, data[3] if data[3] is not None else '')

    ttk.Button(update_window, text='Update', command=save_update).pack(pady=12)

def search_book():
    if not check_connection(): return

    def search_data():
        key = search_entry.get().strip()
        if key == '':
            messagebox.showerror('Error', 'Enter search term', parent=search_window)
            return
        # Try numeric search for year, else string fields
        try:
            possible_year = int(key)
        except ValueError:
            possible_year = None

        query = """
            SELECT * FROM books
            WHERE ISBN=%s OR Title LIKE %s OR Author LIKE %s {year_clause}
        """.format(year_clause="OR Year=%s" if possible_year is not None else "")

        params = (key, f"%{key}%", f"%{key}%")
        if possible_year is not None:
            params = (key, f"%{key}%", f"%{key}%", possible_year)

        mycursor.execute(query, params)
        rows = mycursor.fetchall()
        bookTable.delete(*bookTable.get_children())
        for row in rows:
            bookTable.insert('', END, values=row)
        if not rows:
            messagebox.showinfo('Info', 'No record found', parent=search_window)

    search_window = Toplevel()
    search_window.title('Search')
    search_window.geometry('450x140')
    search_window.grab_set()
    Label(search_window, text='Enter ISBN/Title/Author/Year').pack(pady=6)
    search_entry = Entry(search_window, width=50)
    search_entry.pack(pady=6)
    ttk.Button(search_window, text='Search', command=search_data).pack(pady=10)

def export_data():
    if not check_connection(): return

    data = bookTable.get_children()
    if not data:
        messagebox.showerror("Error", "No data to export!", parent=root)
        return

    file_path = filedialog.asksaveasfilename(defaultextension='.csv', filetypes=[('CSV files', '*.csv')])
    if not file_path:
        return

    try:
        with open(file_path, mode='w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['ISBN','Title','Author','Year','Added_Date','Added_Time'])
            for row_id in data:
                writer.writerow(bookTable.item(row_id)['values'])
        messagebox.showinfo("Success", f"Data exported successfully to\n{file_path}", parent=root)
    except Exception as e:
        messagebox.showerror('Error', f'Export failed: {e}', parent=root)

def exit_program():
    if messagebox.askyesno("Confirm Exit", "Are you sure you want to exit?", parent=root):
        root.destroy()

# ========================== UI Functions ==========================
def clock():
    datetimelabel.config(text=f'    Date: {time.strftime("%d/%m/%Y")}\n Time: {time.strftime("%H:%M:%S")}')
    datetimelabel.after(1000, clock)

def slider():
    global text, count
    text += s[count]
    sliderlabel.config(text=text)
    count += 1
    if count < len(s):
        sliderlabel.after(200, slider)
    else:
        # restart sliding after a pause
        def restart():
            global text, count
            text = ''
            count = 0
            sliderlabel.config(text='')
            slider()
        sliderlabel.after(1200, restart)

def enable_drag_selection(treeview):
    treeview._drag_start = None

    def on_button_press(event):
        row = treeview.identify_row(event.y)
        if row:
            current_selection = treeview.selection()
            if row not in current_selection:
                treeview.selection_set(row)
            treeview._drag_start = row

    def on_mouse_drag(event):
        if treeview._drag_start:
            row = treeview.identify_row(event.y)
            if row:
                start = treeview.index(treeview._drag_start)
                end = treeview.index(row)
                if start > end:
                    start, end = end, start
                children = treeview.get_children('')
                treeview.selection_set(children[start:end + 1])

    def on_button_release(event):
        treeview._drag_start = None

    treeview.bind("<ButtonPress-1>", on_button_press)
    treeview.bind("<B1-Motion>", on_mouse_drag)
    treeview.bind("<ButtonRelease-1>", on_button_release)

# ========================== GUI Setup ==========================
root = ttkthemes.ThemedTk()
root.get_themes()
root.set_theme('winnative')
root.title('Library Management System')
root.geometry('1174x680+100+20')
root.resizable(width=False, height=False)

# Clock & Slider
datetimelabel = Label(root, text='Date and Time', font=('times new roman',15,'bold'), fg='green')
datetimelabel.place(x=40, y=10)
clock()

s = 'Library Management System'
text = ''
count = 0
sliderlabel = Label(root, text='', font=('arial',20,'bold'),fg='navy')
sliderlabel.place(x=500, y=30)
slider()

# Connect Button
ttk.Button(root, text='Connect to database', command=connect_database, cursor='hand2').place(x=1000, y=30)

# Left Frame (Buttons)
leftframe = Frame(root)
leftframe.place(x=50, y=90, width=300, height=560)

try:
    logo_image = PhotoImage(file='Library.png')
    Label(leftframe, image=logo_image).grid(row=0, column=0)
except Exception:
    Label(leftframe, text='[No Logo]', font=('arial', 15, 'bold')).grid(row=0, column=0, pady=10)

addBookButton = ttk.Button(leftframe, text='Add Book', cursor='hand2', width=25, state=DISABLED, command=add_book)
searchBookButton = ttk.Button(leftframe, text='Search Book', cursor='hand2', width=25, state=DISABLED, command=search_book)
deleteBookButton = ttk.Button(leftframe, text='Delete Book', cursor='hand2', width=25, state=DISABLED, command=delete_book)
updateBookButton = ttk.Button(leftframe, text='Update Book', cursor='hand2', width=25, state=DISABLED, command=update_book)
showBookButton = ttk.Button(leftframe, text='Show Books', cursor='hand2', width=25, state=DISABLED, command=show_books)
exportBookButton = ttk.Button(leftframe, text='Export Data', cursor='hand2', width=25, state=DISABLED, command=export_data)
exitButton = ttk.Button(leftframe, text='Exit', cursor='hand2', width=25, command=exit_program)

for i, btn in enumerate([addBookButton, searchBookButton, deleteBookButton,
                         updateBookButton, showBookButton, exportBookButton, exitButton], start=1):
    btn.grid(row=i, column=0, pady=12)

# Right Frame (Book Table)
rightframe = Frame(root)
rightframe.place(x=370, y=90, width=780, height=560)

scrollbarx = Scrollbar(rightframe, orient=HORIZONTAL)
scrollbary = Scrollbar(rightframe, orient=VERTICAL)
bookTable = ttk.Treeview(
    rightframe,
    columns=('ISBN','Title','Author','Year','Added_Date','Added_Time'),
    xscrollcommand=scrollbarx.set,
    yscrollcommand=scrollbary.set,
    selectmode='extended'
)
scrollbary.pack(side=RIGHT, fill=Y)
scrollbarx.pack(side=BOTTOM, fill=X)
bookTable.pack(fill='both', expand=True)
scrollbarx.config(command=bookTable.xview)
scrollbary.config(command=bookTable.yview)
bookTable['show'] = 'headings'

for col in bookTable['columns']:
    bookTable.heading(col, text=col.replace('_', ' '))
    # give Title wider column
    if col == 'Title':
        bookTable.column(col, width=300, anchor=CENTER)
    else:
        bookTable.column(col, width=120, anchor=CENTER)

enable_drag_selection(bookTable)

root.mainloop()
