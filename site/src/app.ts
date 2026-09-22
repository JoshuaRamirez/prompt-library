import { Application, type Component } from 'vanilla-mvc';
import { ApplicationDomain } from './application/application-domain.ts';
import { SitePageComponent } from './components/site-page/site-page.component.ts';

/** The root: the bus, the application domain and the page. */
export class SiteApplication extends Application<ApplicationDomain> {
  protected createDomain(): ApplicationDomain { return new ApplicationDomain(); }
  protected createShell(): Component { return new SitePageComponent('site-page'); }
}
