import { Controller } from 'vanilla-mvc';
import type { ApplicationDomain } from '../../application/application-domain.ts';
import type { SitePageModel } from './site-page.model.ts';

export class SitePageController extends Controller<SitePageModel, ApplicationDomain> {
  protected createModel(): SitePageModel {
    return {
      version: '0.1.2',
      repository: 'https://github.com/JoshuaRamirez/prompt-library',
      diagrams: 'diagrams/',
      framework: 'https://github.com/JoshuaRamirez/vanilla-mvc',
    };
  }
}
