
import pandas as pd
import matplotlib.pyplot as plt
import re
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from tkinter import Tk, Label, Button, Entry, filedialog, Text, Scrollbar, RIGHT, Y, Frame, Canvas
from matplotlib.backend_bases import PickEvent

class KeywordSearchApp:
    def __init__(self, master):
        self.master = master
        master.title("Email Keyword Search")
        
        self.label = Label(master, text="Enter Keywords (comma separated):")
        self.label.pack()
        
        self.entry = Entry(master)
        self.entry.pack()
        
        self.load_button = Button(master, text="Load DataFrame", command=self.load_dataframe)
        self.load_button.pack()

        self.search_button = Button(master, text="Search", command=self.plot_keywords)
        self.search_button.pack()

        self.refresh_button = Button(master, text="Refresh", command=self.refresh)
        self.refresh_button.pack()

        self.detail_frame = Frame(master)
        self.detail_frame.pack()

        self.date_sent_text = self.create_text_widget("Date Sent:")
        self.subject_text = self.create_text_widget("Subject:")
        self.from_text = self.create_text_widget("From:")
        self.to_text = self.create_text_widget("To:")
        self.body_text = self.create_text_widget("Cleaned Body:", height=10)

        self.df = None
        self.email_data_dict = {}
        self.canvas = None

    def create_text_widget(self, label_text, height=2):
        label = Label(self.detail_frame, text=label_text)
        label.pack(side="top")
        text_widget = Text(self.detail_frame, wrap='word', width=100, height=height)
        text_widget.pack(side="top")
        return text_widget

    def load_dataframe(self):
        file_path = filedialog.askopenfilename(title="Select the DataFrame CSV file", filetypes=[("CSV files", "*.csv")])
        if file_path:
            self.df = pd.read_csv(file_path, encoding='ISO-8859-1')
            print(f"Loaded DataFrame from {file_path}")

    def refresh(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
        self.entry.delete(0, 'end')
        self.plot_keywords()

    def plot_keywords(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()

        keyword_input = self.entry.get()
        keywords = [k.strip().lower() for k in keyword_input.split(',')]

        def score_email(email_body):
            if isinstance(email_body, str):
                email_body_lower = email_body.lower()
                words = set(email_body_lower.split())  # Convert to set for faster lookup
                score = 0
                for keyword in keywords:
                    keyword_lower = keyword.lower()
                    if keyword_lower in words:
                        score += len(keyword_lower)
                return score
            else:
                return 0

        self.df['Keyword_Score'] = self.df['Cleaned_Body'].apply(score_email)
        top_emails = self.df.nlargest(50, 'Keyword_Score')
        top_emails['Date Sent'] = pd.to_datetime(top_emails['Date Sent'], errors='coerce')
        top_emails_sorted = top_emails.sort_values('Date Sent')
        sender_count_keywords = top_emails_sorted['From (display)'].value_counts()

        fig, ax = plt.subplots(figsize=(15, 8))
        for sender in sender_count_keywords.index:
            subset = top_emails_sorted[top_emails_sorted['From (display)'] == sender]
            line, = ax.plot(subset['Date Sent'], [sender] * len(subset), 'o', label=sender, picker=5)
            self.email_data_dict[line] = subset

        ax.set_xlabel('Date')
        ax.set_ylabel('Sender')
        fig.canvas.mpl_connect('pick_event', self.onpick)

        self.canvas = FigureCanvasTkAgg(fig, master=self.master)
        toolbar = NavigationToolbar2Tk(self.canvas, self.master)
        toolbar.update()
        self.canvas.get_tk_widget().pack(side=RIGHT)
        self.canvas.draw()

    def onpick(self, event: PickEvent):
        self.date_sent_text.delete("1.0", "end")
        self.subject_text.delete("1.0", "end")
        self.from_text.delete("1.0", "end")
        self.to_text.delete("1.0", "end")
        self.body_text.delete("1.0", "end")

        ind = event.ind[0]
        email_row = self.email_data_dict[event.artist].iloc[ind]
        self.date_sent_text.insert("end", email_row['Date Sent'].strftime('%m/%d/%y %H:%M:%S'))
        self.subject_text.insert("end", email_row['Subject'])
        self.from_text.insert("end", email_row.get('From (display)', 'N/A'))
        self.to_text.insert("end", email_row.get('To (display)', 'N/A'))
        self.body_text.insert("end", email_row.get('Cleaned_Body', 'N/A'))

if __name__ == "__main__":
    root = Tk()
    app = KeywordSearchApp(root)
    root.mainloop()
