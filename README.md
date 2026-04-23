🧠 AI Storage Manager Pro
I built this because I was tired of AI models and VFX caches eating my SSD for breakfast. It’s a fast Python tool to find and kill the heavy "ghost" files that Windows Disk Cleanup usually misses.

What it actually does:

Smart Temp Detection: It’s not dumb—it knows the difference between a real Windows junk folder and a folder you manually named "temp" for a project.


Finds AI Weights: It automatically pulls up the massive blobs from Ollama, ComfyUI, and Chrome AI so you can see where your GBs went.


Fast Scanning: I rebuilt the scanner with a custom grouping logic so it won't freeze your PC, even if you do a 0MB deep scan on a full C: drive.


No Folder Inception: It hides the "Russian Doll" effect where you have to click through 10 folders to find the one actually taking up space.

Safety Lock: It won't let you touch EFI or critical system files. It's built to clean your storage, not brick your PC.

🛠️ Setup:
Make sure you have Python installed.

Throw AIStorageManagerPro.py and LaunchCleaner.bat in the same folder.

Run the .bat file and start clearing space.
