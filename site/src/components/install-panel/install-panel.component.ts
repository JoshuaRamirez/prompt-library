import { Component } from 'vanilla-mvc';
import { InstallPanelController } from './install-panel.controller.ts';
import type { InstallPanelModel } from './install-panel.model.ts';
import { installPanelTemplate } from './install-panel.template.ts';

export class InstallPanelComponent extends Component<InstallPanelModel, InstallPanelController> {
  protected createTemplate() { return installPanelTemplate; }
  protected createController() { return new InstallPanelController(); }
}
