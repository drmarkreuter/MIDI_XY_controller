import tkinter as tk
from tkinter import ttk, messagebox
import pygame.midi
import threading
import time

class XYMidiController:
    def __init__(self):
        # Initialize pygame MIDI
        pygame.midi.init()
        self.midi_out = None
        self.midi_channel = 0  # MIDI channel 1 (0-indexed)
        
        # Controller state
        self.x_cc = 78  # Default X CC value
        self.y_cc = 77  # Default Y CC value
        self.current_x_value = 64  # Current X MIDI value (0-127)
        self.current_y_value = 64  # Current Y MIDI value (0-127)
        self.is_dragging = False
        
        # Setup UI
        self.setup_ui()
        self.setup_midi()
        
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("XY MIDI Controller")
        self.root.geometry("600x550")
        self.root.configure(bg='#f0f0f0')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # XY Pad Frame
        pad_frame = ttk.LabelFrame(main_frame, text="XY Pad", padding="10")
        pad_frame.grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # XY Pad Canvas
        self.canvas = tk.Canvas(pad_frame, width=400, height=250, bg='white', 
                               relief='sunken', bd=2)
        self.canvas.grid(row=0, column=0, padx=5, pady=5)
        
        # Bind mouse events
        self.canvas.bind('<Button-1>', self.on_mouse_down)
        self.canvas.bind('<B1-Motion>', self.on_mouse_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_mouse_up)
        
        # Draw initial crosshair
        self.draw_crosshair()
        
        # CC Value inputs frame
        cc_frame = ttk.LabelFrame(main_frame, text="CC Values", padding="10")
        cc_frame.grid(row=1, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Y CC input
        ttk.Label(cc_frame, text="Y CC value:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.y_cc_var = tk.StringVar(value=str(self.y_cc))
        y_cc_entry = ttk.Entry(cc_frame, textvariable=self.y_cc_var, width=10)
        y_cc_entry.grid(row=0, column=1, padx=5)
        y_cc_entry.bind('<Return>', self.update_y_cc)
        y_cc_entry.bind('<FocusOut>', self.update_y_cc)
        
        # X CC input
        ttk.Label(cc_frame, text="X CC value:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.x_cc_var = tk.StringVar(value=str(self.x_cc))
        x_cc_entry = ttk.Entry(cc_frame, textvariable=self.x_cc_var, width=10)
        x_cc_entry.grid(row=1, column=1, padx=5)
        x_cc_entry.bind('<Return>', self.update_x_cc)
        x_cc_entry.bind('<FocusOut>', self.update_x_cc)
        
        # MIDI Device Selection
        midi_frame = ttk.LabelFrame(main_frame, text="MIDI Output", padding="10")
        midi_frame.grid(row=2, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        ttk.Label(midi_frame, text="MIDI Device:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.midi_var = tk.StringVar()
        self.midi_combo = ttk.Combobox(midi_frame, textvariable=self.midi_var, 
                                      state="readonly", width=30)
        self.midi_combo.grid(row=0, column=1, padx=5)
        self.midi_combo.bind('<<ComboboxSelected>>', self.on_midi_device_change)
        
        # Refresh MIDI devices button
        ttk.Button(midi_frame, text="Refresh", 
                  command=self.refresh_midi_devices).grid(row=0, column=2, padx=5)
        
        # MIDI Channel Selection
        ttk.Label(midi_frame, text="MIDI Channel:").grid(row=1, column=0, padx=5, sticky=tk.W)
        self.channel_var = tk.StringVar(value="1")
        self.channel_combo = ttk.Combobox(midi_frame, textvariable=self.channel_var,
                                         values=[str(i) for i in range(1, 17)],
                                         state="readonly", width=10)
        self.channel_combo.grid(row=1, column=1, padx=5, sticky=tk.W)
        self.channel_combo.bind('<<ComboboxSelected>>', self.on_midi_channel_change)
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="Status: Ready")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.values_label = ttk.Label(status_frame, text="X: 64, Y: 64")
        self.values_label.grid(row=0, column=1, sticky=tk.E)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        status_frame.columnconfigure(1, weight=1)
        
    def setup_midi(self):
        """Initialize MIDI and populate device list"""
        self.refresh_midi_devices()
        
    def refresh_midi_devices(self):
        """Refresh the list of available MIDI output devices"""
        devices = []
        device_count = pygame.midi.get_count()
        
        for i in range(device_count):
            device_info = pygame.midi.get_device_info(i)
            # device_info: (interf, name, input, output, opened)
            if device_info[3]:  # if output device
                device_name = device_info[1].decode('utf-8')
                devices.append(f"{i}: {device_name}")
        
        self.midi_combo['values'] = devices
        if devices and not self.midi_var.get():
            self.midi_combo.current(0)
            self.on_midi_device_change(None)
    
    def on_midi_channel_change(self, event=None):
        """Handle MIDI channel selection change"""
        try:
            channel_str = self.channel_var.get()
            if channel_str:
                self.midi_channel = int(channel_str) - 1  # Convert to 0-indexed
        except ValueError:
            self.midi_channel = 0  # Default to channel 1
    
    def on_midi_device_change(self, event):
        """Handle MIDI device selection change"""
        try:
            if self.midi_out:
                self.midi_out.close()
            
            device_str = self.midi_var.get()
            if device_str:
                device_id = int(device_str.split(':')[0])
                self.midi_out = pygame.midi.Output(device_id)
                self.status_label.config(text=f"Status: Connected to {device_str}")
            else:
                self.midi_out = None
                self.status_label.config(text="Status: No device selected")
        except Exception as e:
            messagebox.showerror("MIDI Error", f"Failed to open MIDI device: {str(e)}")
            self.status_label.config(text="Status: Connection failed")
    
    def draw_crosshair(self):
        """Draw crosshair on canvas based on current X,Y values"""
        self.canvas.delete("crosshair")
        
        # Convert MIDI values (0-127) to canvas coordinates
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Handle case where canvas hasn't been drawn yet
        if canvas_width <= 1:
            canvas_width = 400
        if canvas_height <= 1:
            canvas_height = 250
            
        x = (self.current_x_value / 127.0) * canvas_width
        y = canvas_height - (self.current_y_value / 127.0) * canvas_height  # Invert Y
        
        # Draw crosshair lines
        self.canvas.create_line(x-10, y, x+10, y, fill="red", width=2, tags="crosshair")
        self.canvas.create_line(x, y-10, x, y+10, fill="red", width=2, tags="crosshair")
        
        # Draw center circle
        self.canvas.create_oval(x-3, y-3, x+3, y+3, fill="red", tags="crosshair")
        
    def on_mouse_down(self, event):
        """Handle mouse press on XY pad"""
        self.is_dragging = True
        self.update_position(event.x, event.y)
        
    def on_mouse_drag(self, event):
        """Handle mouse drag on XY pad"""
        if self.is_dragging:
            self.update_position(event.x, event.y)
            
    def on_mouse_up(self, event):
        """Handle mouse release on XY pad"""
        self.is_dragging = False
        
    def update_position(self, canvas_x, canvas_y):
        """Update position based on canvas coordinates"""
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        # Clamp coordinates to canvas bounds
        canvas_x = max(0, min(canvas_width, canvas_x))
        canvas_y = max(0, min(canvas_height, canvas_y))
        
        # Convert to MIDI values (0-127)
        self.current_x_value = int((canvas_x / canvas_width) * 127)
        self.current_y_value = int(((canvas_height - canvas_y) / canvas_height) * 127)  # Invert Y
        
        # Clamp MIDI values
        self.current_x_value = max(0, min(127, self.current_x_value))
        self.current_y_value = max(0, min(127, self.current_y_value))
        
        # Update display
        self.draw_crosshair()
        self.values_label.config(text=f"X: {self.current_x_value}, Y: {self.current_y_value}")
        
        # Send MIDI CC
        self.send_midi_cc()
        
    def send_midi_cc(self):
        """Send MIDI CC messages for current X,Y values"""
        if self.midi_out:
            try:
                # Send X CC
                self.midi_out.write_short(0xB0 | self.midi_channel, self.x_cc, self.current_x_value)
                # Send Y CC
                self.midi_out.write_short(0xB0 | self.midi_channel, self.y_cc, self.current_y_value)
            except Exception as e:
                print(f"MIDI send error: {e}")
                
    def update_x_cc(self, event=None):
        """Update X CC number from input field"""
        try:
            new_cc = int(self.x_cc_var.get())
            if 0 <= new_cc <= 127:
                self.x_cc = new_cc
            else:
                messagebox.showerror("Invalid CC", "CC values must be between 0 and 127")
                self.x_cc_var.set(str(self.x_cc))
        except ValueError:
            messagebox.showerror("Invalid CC", "Please enter a valid number")
            self.x_cc_var.set(str(self.x_cc))
            
    def update_y_cc(self, event=None):
        """Update Y CC number from input field"""
        try:
            new_cc = int(self.y_cc_var.get())
            if 0 <= new_cc <= 127:
                self.y_cc = new_cc
            else:
                messagebox.showerror("Invalid CC", "CC values must be between 0 and 127")
                self.y_cc_var.set(str(self.y_cc))
        except ValueError:
            messagebox.showerror("Invalid CC", "Please enter a valid number")
            self.y_cc_var.set(str(self.y_cc))
    
    def run(self):
        """Start the application"""
        # Update crosshair after window is fully rendered
        self.root.after(100, self.draw_crosshair)
        self.root.mainloop()
        
    def cleanup(self):
        """Clean up MIDI resources"""
        if self.midi_out:
            self.midi_out.close()
        pygame.midi.quit()

if __name__ == "__main__":
    try:
        app = XYMidiController()
        app.run()
    except KeyboardInterrupt:
        pass
    finally:
        if 'app' in locals():
            app.cleanup()