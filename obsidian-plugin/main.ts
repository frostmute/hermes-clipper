import { Plugin, Notice, TFile, WorkspaceLeaf } from 'obsidian';

interface ClipperSettings {
	bridgeUrl: string;
}

const DEFAULT_SETTINGS: ClipperSettings = {
	bridgeUrl: 'http://127.0.0.1:8088'
}

export default class HermesClipperPlugin extends Plugin {
	settings: ClipperSettings;
	statusBarItemEl: HTMLElement;

	async onload() {
		await this.loadSettings();

		this.statusBarItemEl = this.addStatusBarItem();
		this.statusBarItemEl.setText('Hermes: Idle');

		this.addRibbonIcon('brain', 'Hermes: Synthesize & Organize', () => {
			this.synthesizeNote();
		});

		this.addCommand({
			id: 'hermes-synthesize-current',
			name: 'Synthesize Current Note',
			callback: () => this.synthesizeNote()
		});
	}

	async synthesizeNote() {
		const activeFile = this.app.workspace.getActiveFile();
		if (!(activeFile instanceof TFile)) {
			new Notice('Hermes: No file selected. Try using your eyes.');
			return;
		}

		new Notice(`Hermes: Dispatching for ${activeFile.name}...`);
		this.statusBarItemEl.setText('Hermes: 🧠 Synthesizing...');

		try {
			const response = await fetch(`${this.settings.bridgeUrl}/agent/synthesize`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					path: activeFile.path,
					prompt: "Synthesize and organize."
				})
			});

			const data = await response.json();
			if (data.status === 'accepted') {
				this.pollTask(data.task_id);
			} else {
				new Notice('Hermes rejected you: ' + data.message);
				this.statusBarItemEl.setText('Hermes: Idle');
			}
		} catch (err) {
			new Notice('Failed to connect to Hermes Bridge.');
			this.statusBarItemEl.setText('Hermes: Idle');
		}
	}

	async pollTask(taskId: string) {
		const check = async () => {
			try {
				const response = await fetch(`${this.settings.bridgeUrl}/tasks/${taskId}`);
				const task = await response.json();

				if (task.status === 'completed') {
					this.statusBarItemEl.setText('Hermes: Idle');
					new Notice('Hermes: Synthesis complete. Note moved.');
					
					// If Hermes moved the file, we should try to find it
					if (task.result && task.result.path) {
						this.openNewPath(task.result.path);
					}
					return true;
				} else if (task.status === 'failed') {
					this.statusBarItemEl.setText('Hermes: Failed');
					new Notice('Hermes: I failed. It happens to the best of us.');
					return true;
				}
				return false;
			} catch (err) {
				return true; // Stop on error
			}
		};

		const interval = setInterval(async () => {
			if (await check()) clearInterval(interval);
		}, 3000);
	}

	async openNewPath(absPath: string) {
		// Convert absolute path to vault relative path
		// Bridge returns absolute path, Obsidian needs vault relative
		const vaultPath = (this.app.vault.adapter as any).getBasePath();
		let relPath = absPath.replace(vaultPath, '').replace(/^\//, '');
		
		const file = this.app.vault.getAbstractFileByPath(relPath);
		if (file instanceof TFile) {
			this.app.workspace.getLeaf(true).openFile(file);
		}
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}
}
