import tkinter as tk
from tkinter import ttk, messagebox
import pygame.midi
import threading
import time
import json
import os

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
        
        # Preset management
        self.presets_file = "xy_midi_presets.json"
        self.presets = self.load_presets()
        
        # Setup UI
        self.setup_ui()
        self.setup_midi()
        
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("XY MIDI Controller")
        self.root.geometry("600x650")
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
        
        # Preset Management Frame
        preset_frame = ttk.LabelFrame(main_frame, text="Presets", padding="10")
        preset_frame.grid(row=3, column=0, columnspan=2, pady=(0, 10), sticky=(tk.W, tk.E))
        
        # Preset selection
        ttk.Label(preset_frame, text="Preset:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var,
                                        state="readonly", width=25)
        self.preset_combo.grid(row=0, column=1, padx=5)
        self.preset_combo.bind('<<ComboboxSelected>>', self.load_selected_preset)
        
        # Preset buttons
        ttk.Button(preset_frame, text="Load", 
                  command=self.load_selected_preset).grid(row=0, column=2, padx=5)
        ttk.Button(preset_frame, text="Save", 
                  command=self.show_save_preset_dialog).grid(row=0, column=3, padx=5)
        ttk.Button(preset_frame, text="Delete", 
                  command=self.delete_selected_preset).grid(row=0, column=4, padx=5)
        
        # Update preset list
        self.update_preset_list()
        
        # Status frame
        status_frame = ttk.Frame(main_frame)
        status_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
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
    
    def load_presets(self):
        """Load presets from JSON file"""
        default_presets = {
            "SH01A filter": {"x_cc": 74, "y_cc": 71, "channel": 1}
        }
        
        try:
            if os.path.exists(self.presets_file):
                with open(self.presets_file, 'r') as f:
                    presets = json.load(f)
                # Ensure default preset exists
                if "SH01A filter" not in presets:
                    presets["SH01A filter"] = default_presets["SH01A filter"]
                return presets
            else:
                # Create file with default presets
                self.save_presets_to_file(default_presets)
                return default_presets
        except Exception as e:
            print(f"Error loading presets: {e}")
            return default_presets
    
    def save_presets_to_file(self, presets=None):
        """Save presets to JSON file"""
        try:
            presets_to_save = presets if presets is not None else self.presets
            with open(self.presets_file, 'w') as f:
                json.dump(presets_to_save, f, indent=2)
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save presets: {str(e)}")
    
    def update_preset_list(self):
        """Update the preset combobox with current presets"""
        preset_names = list(self.presets.keys())
        self.preset_combo['values'] = preset_names
        if preset_names and not self.preset_var.get():
            self.preset_combo.current(0)
    
    def load_selected_preset(self, event=None):
        """Load the selected preset"""
        preset_name = self.preset_var.get()
        if preset_name and preset_name in self.presets:
            preset = self.presets[preset_name]
            
            # Update CC values
            self.x_cc = preset['x_cc']
            self.y_cc = preset['y_cc']
            self.x_cc_var.set(str(self.x_cc))
            self.y_cc_var.set(str(self.y_cc))
            
            # Update channel
            channel = preset.get('channel', 1)
            self.channel_var.set(str(channel))
            self.midi_channel = channel - 1  # Convert to 0-indexed
            
            self.status_label.config(text=f"Status: Loaded preset '{preset_name}'")
    
    def show_save_preset_dialog(self):
        """Show dialog to save current settings as preset"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Save Preset")
        dialog.geometry("300x120")
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog
        dialog.geometry("+%d+%d" % (self.root.winfo_rootx() + 150, 
                                   self.root.winfo_rooty() + 100))
        
        ttk.Label(dialog, text="Preset Name:").pack(pady=10)
        
        name_var = tk.StringVar()
        name_entry = ttk.Entry(dialog, textvariable=name_var, width=30)
        name_entry.pack(pady=5)
        name_entry.focus()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        def save_preset():
            name = name_var.get().strip()
            if not name:
                messagebox.showerror("Error", "Please enter a preset name")
                return
            
            # Save current settings
            self.presets[name] = {
                'x_cc': self.x_cc,
                'y_cc': self.y_cc,
                'channel': int(self.channel_var.get())
            }
            
            self.save_presets_to_file()
            self.update_preset_list()
            
            # Select the newly saved preset
            self.preset_var.set(name)
            
            self.status_label.config(text=f"Status: Saved preset '{name}'")
            dialog.destroy()
        
        def cancel():
            dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_preset).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key to save
        dialog.bind('<Return>', lambda e: save_preset())
        name_entry.bind('<Return>', lambda e: save_preset())
    
    def delete_selected_preset(self):
        """Delete the selected preset"""
        preset_name = self.preset_var.get()
        if not preset_name:
            messagebox.showwarning("Warning", "Please select a preset to delete")
            return
        
        if preset_name == "SH01A filter":
            messagebox.showwarning("Warning", "Cannot delete the default preset")
            return
        
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete preset '{preset_name}'?"):
            del self.presets[preset_name]
            self.save_presets_to_file()
            self.update_preset_list()
            self.status_label.config(text=f"Status: Deleted preset '{preset_name}'")
    
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