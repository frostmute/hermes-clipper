import { Plugin, Notice, TFile } from 'obsidian';

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

		// Add Ribbon Icon (Toolbar Button)
		this.addRibbonIcon('brain', 'Hermes: Synthesize & Organize', (evt: MouseEvent) => {
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
			new Notice('No active file to synthesize.');
			return;
		}

		new Notice(`Dispatching Hermes to synthesize: ${activeFile.name}...`);
		this.statusBarItemEl.setText('Hermes: 🧠 Synthesizing...');

		try {
			const response = await fetch(`${this.settings.bridgeUrl}/agent/synthesize`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({
					path: activeFile.path,
					prompt: "Synthesize and refine this note."
				})
			});

			const data = await response.json();
			if (data.status === 'success') {
				new Notice('Synthesis complete!');
			} else {
				new Notice('Hermes failed: ' + data.message);
			}
		} catch (err) {
			new Notice('Failed to connect to Hermes Bridge.');
			console.error(err);
		} finally {
			this.statusBarItemEl.setText('Hermes: Idle');
		}
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
	}
}
