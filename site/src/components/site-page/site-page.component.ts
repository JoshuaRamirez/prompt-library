import { Component } from 'vanilla-mvc';
import { InstallPanelComponent } from '../install-panel/install-panel.component.ts';
import { PromptComposerComponent } from '../prompt-composer/prompt-composer.component.ts';
import { PromptFinderComponent } from '../prompt-finder/prompt-finder.component.ts';
import { SitePageController } from './site-page.controller.ts';
import type { SitePageModel } from './site-page.model.ts';
import { sitePageTemplate } from './site-page.template.ts';

export class SitePageComponent extends Component<SitePageModel, SitePageController> {
  protected createTemplate() { return sitePageTemplate; }
  protected createController() { return new SitePageController(); }
  protected override createChildren() {
    return [
      new InstallPanelComponent('install-panel'),
      new PromptFinderComponent('prompt-finder'),
      new PromptComposerComponent('prompt-composer'),
    ];
  }
}
