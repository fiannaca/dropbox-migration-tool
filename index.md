---
layout: default
title: Home
---

<section id="introduction">
    <h2>Introduction</h2>
    <p>This command-line utility is designed to help users migrate their files and folders from a Dropbox account to a Google Drive account. It is built to be robust, with features like resumable migrations, conflict resolution, and different modes of operation to suit various user needs.</p>
</section>

<section id="features">
    <h2>Key Features</h2>
    <ul>
        <li><strong>Resumable Migrations:</strong> If the script is interrupted, it can be restarted and will resume where it left off.</li>
        <li><strong>Conflict Resolution:</strong> Intelligently handles cases where files or folders with the same name already exist in the destination.</li>
        <li><strong>Interactive Mode:</strong> An optional <code>--interactive</code> flag allows you to confirm the migration for each folder.</li>
        <li><strong>Test Runs:</strong> An optional <code>--test_run</code> flag lets you perform a dry run on a small batch of files.</li>
        <li><strong>Robust Error Handling:</strong> Automatically retries on common API errors like rate limiting.</li>
    </ul>
</section>

<section id="installation">
    <h2>Installation</h2>
    <pre><code># 1. Clone the repository
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name

# 2. Install dependencies
pip install -r requirements.txt</code></pre>
</section>

<section id="configuration">
    <h2>Configuration</h2>
    <p>The tool requires API credentials from both Dropbox and Google.</p>
    
    <h3>Dropbox Credentials</h3>
    <ol>
        <li>Go to the <a href="https://www.dropbox.com/developers/apps" target="_blank">Dropbox App Console</a> and create a new app.</li>
        <li>Choose the "Scoped access" API and "Full Dropbox" access.</li>
        <li>Give your app a unique name.</li>
        <li>In the "Permissions" tab, check the following scopes: <code>files.content.read</code>, <code>files.content.write</code>, and <code>files.metadata.read</code>.</li>
        <li>From the "Settings" tab, get your "App key" and "App secret".</li>
    </ol>

    <h3>Google Drive Credentials</h3>
    <ol>
        <li>Go to the <a href="https://console.cloud.google.com/" target="_blank">Google Cloud Console</a> and create a new project.</li>
        <li>Enable the "Google Drive API" for your project.</li>
        <li>Go to "Credentials", click "Create Credentials", and choose "OAuth client ID".</li>
        <li>Select "Desktop app" as the application type.</li>
        <li>Download the credentials JSON file, rename it to <code>google_credentials.json</code>, and place it in the project's root directory.</li>
    </ol>

    <h3>Providing Credentials to the Tool</h3>
    <p>You can provide your Dropbox credentials using either a configuration file or environment variables.</p>
    <ul>
        <li><strong>Config File (Recommended):</strong> Rename <code>config.ini.template</code> to <code>config.ini</code> and add your app key and secret.</li>
        <li><strong>Environment Variables:</strong> Set <code>DROPBOX_APP_KEY</code> and <code>DROPBOX_APP_SECRET</code>. These will override the config file.</li>
    </ul>
</section>

<section id="usage">
    <h2>Usage</h2>
    <p>The tool is run from the command line.</p>
    <pre><code># For a standard, full migration
python3 src/main.py

# For a test run of the first 10 files
python3 src/main.py --test_run

# For an interactive run with folder-by-folder confirmation
python3 src/main.py --interactive</code></pre>
</section>

<section id="faq">
    <h2>FAQ & Troubleshooting</h2>
    <dl>
        <dt>What happens if the migration is interrupted?</dt>
        <dd>Simply run the script again. The tool saves its state and will resume where it left off, avoiding duplicate transfers.</dd>

        <dt>I'm getting an API error when I first run the tool.</dt>
        <dd>Double-check that your API credentials in <code>config.ini</code> (or environment variables) and <code>google_credentials.json</code> are correct. Ensure you have enabled the correct permissions/scopes in both the Dropbox and Google Cloud consoles.</dd>

        <dt>The migration seems slow.</dt>
        <dd>For accounts with many files, the migration can take a long time. This is usually due to the rate limits imposed by the Dropbox and Google Drive APIs. The tool handles these limits automatically by pausing and retrying, so it's best to let it run to completion.</dd>

        <dt>How can I reset the migration and start over?</dt>
        <dd>Delete the <code>migration_state.json</code> file from the root directory. This will remove all progress tracking.</dd>
    </dl>
</section>
