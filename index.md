---
layout: default
title: Home
---

<section id="introduction">
    <h2>Introduction</h2>
    <p>A robust command-line tool to migrate files and folders from Dropbox to Google Drive, with a focus on reliability and a user-friendly experience.</p>
</section>

<section id="features">
    <h2>Key Features</h2>
    <ul>
        <li><strong>Resumable Migrations</strong>: If the script is interrupted, it can be restarted and will automatically resume where it left off.</li>
        <li><strong>Intelligent Conflict Resolution</strong>: Choose to overwrite, rename, or skip files that already exist, and apply your choice to all future conflicts.</li>
        <li><strong>Targeted Migrations</strong>: Use the <code>--src</code> and <code>--dest</code> flags to migrate specific folders.</li>
        <li><strong>Dry Runs</strong>: Use the <code>--dry_run</code> flag to see a plan of what will be migrated without transferring any files.</li>
        <li><strong>Interactive Mode</strong>: Use the <code>--interactive</code> flag to confirm the migration for each folder.</li>
        <li><strong>Robust Error Handling</strong>: Gracefully handles API errors, expired tokens, and reports any failed files at the end of the session.</li>
    </ul>
</section>

<section id="installation">
    <h2>Installation</h2>
    <pre><code># 1. Clone the repository
git clone https://github.com/fiannaca/dropbox-migration-tool.git
cd dropbox-migration-tool

# 2. Install dependencies

pip3 install -r requirements.txt</code></pre>

</section>

<section id="configuration">
    <h2>Configuration</h2>
    <p>The tool requires API credentials from both Dropbox and Google.</p>
    
    <h3>Dropbox Credentials</h3>
    <ol>
        <li>Go to the <a href="https://www.dropbox.com/developers/apps" target="_blank">Dropbox App Console</a> and create a new app with "Scoped access" and "Full Dropbox" permissions.</li>
        <li>In the "Permissions" tab, check: <code>files.content.read</code>, <code>files.content.write</code>, and <code>files.metadata.read</code>.</li>
        <li>Get your "App key" and "App secret" from the "Settings" tab.</li>
    </ol>

    <h3>Google Drive Credentials</h3>
    <ol>
        <li>Go to the <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a> and create a new project.</li>
        <li>Enable the "Google Drive API".</li>
        <li>Create an "OAuth client ID" for a "Desktop app".</li>
        <li>Download the credentials JSON file, rename it to <code>client_secrets.json</code>, and place it in the project's root directory.</li>
    </ol>

    <h3>Providing Credentials to the Tool</h3>
    <p>Provide your Dropbox credentials using either a configuration file (<code>config.ini</code>) or environment variables (<code>DROPBOX_APP_KEY</code>, <code>DROPBOX_APP_SECRET</code>).</p>

</section>

<section id="usage">
    <h2>Usage</h2>
    <p>The tool is run from the command line from the root of the project directory.</p>
    <pre><code># For a standard migration
python3 -m src.main

# For a migration that moves into a specific Google Drive folder

python3 -m src.main --dest "dropbox migration/"

# For a dry run of the first 50 files

python3 -m src.main --dry_run --limit 50

# To migrate a specific folder

python3 -m src.main --src "/My Dropbox Folder" --dest "My Google Drive Folder/Backup"</code></pre>

</section>

<section id="faq">
    <h2>FAQ & Troubleshooting</h2>
    <dl>
        <dt>What happens if the migration is interrupted?</dt>
        <dd>Simply run the script again. The tool saves its state and will resume where it left off.</dd>

        <dt>I'm getting an authentication error.</dt>
        <dd>The tool will attempt to re-authenticate you. If that fails, you may need to delete the <code>dropbox_credentials.json</code> or <code>google_token.json</code> file and run the tool again.</dd>

        <dt>A file failed to migrate. What should I do?</dt>
        <dd>The tool will report any failed files in the final summary. You can review the <code>migration.log</code> file for more detailed error messages.</dd>
    </dl>

</section>
