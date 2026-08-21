# How to Transfer this Project to the Company Computer

Transferring the Weather Data Management System consists of two main parts:
1. **Transferring the Code (the Website)**
2. **Transferring the Database (the Data)**

Follow these steps carefully to ensure a smooth transition without losing any data.

---

## Phase 1: On Your Current Computer

### Step 1: Backup the Database
Since your data lives inside PostgreSQL, simply copying the folder won't copy the data. You must export it.
1. Open **pgAdmin 4** from your Start Menu.
2. In the left panel, expand `Servers` -> `PostgreSQL` -> `Databases`.
3. Right-click on your database (`rmc_chennai_database` or `wdms_db` based on your config).
4. Click **Backup...**
5. Under the "General" tab, set a filename (e.g., `C:\Users\kavin\Desktop\database_backup.sql`).
6. Under "Format", choose **Custom** or **Tar**.
7. Click **Backup**. Wait for the "Backup completed" notification.

### Step 2: Copy the Files
1. Go to your Desktop and locate the **`imd`** folder.
2. Inside the `imd` folder, you can safely **delete** the `venv` folder (the target computer needs its own fresh one) to save space, but it's okay if you leave it.
3. Copy the **`imd`** folder and the **`database_backup.sql`** file you just created onto a USB flash drive.

---

## Phase 2: On the Company Computer

### Step 1: Install Required Software
Before copying the files, the new computer needs the same underlying software:
1. **Python**: Download and install Python 3.9+ from [python.org](https://www.python.org/downloads/). 
   > **CRITICAL**: During the Python installation, you MUST check the box that says **"Add Python to PATH"** at the very bottom of the installer window.
2. **PostgreSQL**: Download and install PostgreSQL from [postgresql.org](https://www.postgresql.org/download/windows/). Remember the password you create during setup!

### Step 2: Copy the Files
1. Plug in your USB drive.
2. Copy the **`imd`** folder onto the Desktop of the company computer.

### Step 3: Setup the Database
1. Open **pgAdmin 4** on the new computer.
2. Expand `Servers` -> `PostgreSQL` -> `Databases`.
3. Right-click `Databases` -> **Create** -> **Database...**
4. Name it exactly what you named it on your computer (e.g., `rmc_chennai_database`). Click Save.
5. Right-click this newly created database and select **Restore...**
6. Select the `database_backup.sql` file from your USB drive.
7. Click **Restore** and wait for it to finish.

### Step 4: Configure the Connection
1. Inside the `imd` folder on the new computer, open the `config.py` file with Notepad.
2. Look for the line `SQLALCHEMY_DATABASE_URI`. 
3. Make sure the password in that link matches the password you just set when installing PostgreSQL on the new computer!
   *(e.g., `postgresql://postgres:YOUR_NEW_PASSWORD@localhost:5432/rmc_chennai_database`)*
4. Save and close the file.

### Step 5: Start the System
1. Inside the `imd` folder, double-click **`setup.bat`**. This will take a few minutes to automatically download all the required libraries for the new computer.
2. Once it says "Setup Complete", close that window.
3. Finally, double-click **`Start_IMD_System.bat`** just like you normally do!

Your website and all its data will now be fully operational on the new machine!
