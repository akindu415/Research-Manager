import statistics
from datetime import datetime
import avro.schema
import avro.io
import io
import hashlib
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog


class ResearchDataManager:
    def __init__(self):
        self.data = []
        self.experiment_counter = 1
        self.schema = avro.schema.parse(open("experiment.avsc").read())

    def add_data(self,experiment_name, date, researcher, data_points):
        entry =[self.experiment_counter,experiment_name, date, researcher, data_points]
        self.data.append(entry)
        print("Data entered successfully")

        self.experiment_counter += 1 #increasing experiment counter when adding new transaction

    #function to view data
    def view_data(self):
        if len(self.data)==0:
            print("No transactions found")
        else:
            for entry in self.data:
                print(entry)

    #function to update data
    def update_data(self,experiment_id, nexperiment_name, ndate, nresearcher, ndata_points):
         for entry in self.data:
            if entry[0] == experiment_id:
                entry[1] = nexperiment_name
                entry[2] = ndate
                entry[3] = nresearcher
                entry[4] = ndata_points
                break
    def delete_data(self,experiment_id):
        self.data = [entry for entry in self.data if entry[0] != experiment_id]

    def get_calculations(self,experiment_id):
        for entry in self.data:
            if entry[0] == experiment_id:
                data_points = entry[4]
                average = sum(data_points) / len(data_points)
                std_dev = statistics.stdev(data_points) if len(data_points) > 1 else 0
                median = statistics.median(data_points)
                return average, std_dev, median
        return None

    def save_experiment(self,filename="experiment_data.avro"):
        bytes_writer = io.BytesIO()
        encoder = avro.io.BinaryEncoder(bytes_writer)
        writer = avro.io.DatumWriter(self.schema)

        for entry in self.data:
            writer.write({
                "experiment_id": entry[0],
                "experiment_name": entry[1],
                "date" :entry[2].strftime("%Y-%m-%d"),
                "researcher":entry[3],
                "data_points":entry[4]
            },encoder)

        serialized_data = bytes_writer.getvalue()

        with open(filename,"wb") as f:
            f.write(serialized_data)

        self._save_checksum(filename)
        print(f"Data saved successfully: {self.data}")
        print("Data saved successfully using avro")

    def load_experiment(self,filename="experiment_data.avro"):
        if not self._verify_checksum(filename):
            print("Data integrity check failed. The file may be corrupted.")
            return

        with open(filename, "rb") as f:
            serialized_data = f.read()

        bytes_reader = io.BytesIO(serialized_data)
        decoder = avro.io.BinaryDecoder(bytes_reader)
        reader = avro.io.DatumReader(self.schema)

        self.data = []
        while bytes_reader.tell() < len(serialized_data):
            experiment = reader.read(decoder)
            self.data.append([
                experiment["experiment_id"],
                experiment["experiment_name"],
                datetime.strptime(experiment["date"], "%Y-%m-%d").date(),
                experiment["researcher"],
                experiment["data_points"]
            ])
            self.experiment_counter = max(self.experiment_counter, experiment["experiment_id"] + 1)

        print(f"Data loaded successfully: {self.data}")
        print("Data loaded successfully using Avro.")

    def _save_checksum(self, filename):
        checksum = hashlib.sha256()
        with open(filename, "rb") as f:
            checksum.update(f.read())
        with open(filename + ".sha256", "w") as f:
            f.write(checksum.hexdigest())

    def _verify_checksum(self, filename):
        checksum = hashlib.sha256()
        with open(filename, "rb") as f:
            checksum.update(f.read())

        try:
            with open(filename + ".sha256", "r") as f:
                stored_checksum = f.read().strip()
        except FileNotFoundError:
            return False

        return checksum.hexdigest() == stored_checksum

class ResearchDataManagerGUI:
    def __init__(self, root, manager):
        self.root = root
        self.manager = manager
        self.root.title("Research Data Management")

        self.tree = ttk.Treeview(root, columns=("ID", "Experiment Name", "Date", "Researcher", "Data Points"), show='headings')
        self.tree.heading("ID", text="ID", command=lambda: self.sort_column("ID", False))
        self.tree.heading("Experiment Name", text="Experiment Name", command=lambda: self.sort_column("Experiment Name", False))
        self.tree.heading("Date", text="Date", command=lambda: self.sort_column("Date", False))
        self.tree.heading("Researcher", text="Researcher", command=lambda: self.sort_column("Researcher", False))
        self.tree.heading("Data Points", text="Data Points", command=lambda: self.sort_column("Data Points", False))
        self.tree.grid(row=0, column=0, columnspan=4, padx=10, pady=10, sticky='nsew')

        self.tree.bind("<ButtonRelease-1>", self.select_item)

        # Search entry
        self.search_entry = tk.Entry(root)
        self.search_entry.grid(row=1, column=0, padx=10, pady=10)
        self.search_entry.bind("<KeyRelease>", self.search)

        # Buttons
        self.add_button = tk.Button(root, text="Add", command=self.add_record)
        self.add_button.grid(row=1, column=1, padx=10, pady=10)

        self.update_button = tk.Button(root, text="Update", command=self.update_record)
        self.update_button.grid(row=1, column=2, padx=10, pady=10)

        self.delete_button = tk.Button(root, text="Delete", command=self.delete_record)
        self.delete_button.grid(row=1, column=3, padx=10, pady=10)

        self.calc_button = tk.Button(root, text="Calculate", command=self.calculate)
        self.calc_button.grid(row=2, column=1, padx=10, pady=10)

        self.load_button = tk.Button(root, text="Load", command=lambda: self.manager.load_experiment("experiment_data.avro"))
        self.load_button.grid(row=2, column=2, padx=10, pady=10)

        self.save_button = tk.Button(root, text="Save", command=lambda: self.manager.save_experiment("experiment_data.avro"))
        self.save_button.grid(row=2, column=3, padx=10, pady=10)

        self.refresh_table()

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for entry in self.manager.data:
            self.tree.insert('', 'end', values=(entry[0], entry[1], entry[2].strftime("%Y-%m-%d"), entry[3], entry[4]))


    def select_item(self, event):
        selected_item = self.tree.selection()
        if selected_item:
            item = self.tree.item(selected_item)
            self.selected_id = int(item['values'][0])

    def add_record(self):
        experiment_name = tk.simpledialog.askstring("Input", "Enter experiment name:")
        date_str = tk.simpledialog.askstring("Input", "Enter date (YYYY-MM-DD):")
        researcher = tk.simpledialog.askstring("Input", "Enter researcher name:")
        data_points_str = tk.simpledialog.askstring("Input", "Enter data points (comma-separated):")

        if experiment_name and date_str and researcher and data_points_str:
            try:
                date = datetime.strptime(date_str, "%Y-%m-%d").date()
                data_points = list(map(int, data_points_str.split(",")))
                self.manager.add_data(experiment_name, date, researcher, data_points)
                self.refresh_table()
            except ValueError:
                messagebox.showerror("Error", "Invalid input format.")

    def update_record(self):
        if hasattr(self, 'selected_id'):
            experiment_name = tk.simpledialog.askstring("Input", "Enter new experiment name:")
            date_str = tk.simpledialog.askstring("Input", "Enter new date (YYYY-MM-DD):")
            researcher = tk.simpledialog.askstring("Input", "Enter new researcher name:")
            data_points_str = tk.simpledialog.askstring("Input", "Enter new data points (comma-separated):")

            if experiment_name and date_str and researcher and data_points_str:
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    data_points = list(map(int, data_points_str.split(",")))
                    self.manager.update_data(self.selected_id, experiment_name, date, researcher, data_points)
                    self.refresh_table()
                except ValueError:
                    messagebox.showerror("Error", "Invalid input format.")
        else:
            messagebox.showerror("Error", "No record selected.")

    def delete_record(self):
        if hasattr(self, 'selected_id'):
            self.manager.delete_data(self.selected_id)
            self.refresh_table()
        else:
            messagebox.showerror("Error", "No record selected.")

    def calculate(self):
        if hasattr(self, 'selected_id'):
            result = self.manager.get_calculations(self.selected_id)
            if result:
                average, std_dev, median = result
                messagebox.showinfo("Calculations", f"Average: {average}\nStandard Deviation: {std_dev}\nMedian: {median}")
            else:
                messagebox.showerror("Error", "No data found for the selected experiment.")
        else:
            messagebox.showerror("Error", "No record selected.")

    def search(self, event):
        query = self.search_entry.get().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        for entry in self.manager.data:
            if query in str(entry).lower():
                self.tree.insert('', 'end', values=entry)

    def sort_column(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)

        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

        self.tree.heading(col, command=lambda: self.sort_column(col, not reverse))

if __name__ == "__main__":
    root = tk.Tk()
    manager = ResearchDataManager()
    gui = ResearchDataManagerGUI(root, manager)
    root.mainloop()
                    
                    
    
    

                


                
