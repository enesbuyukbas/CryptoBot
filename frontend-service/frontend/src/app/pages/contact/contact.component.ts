import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-contact',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './contact.component.html',
  styleUrls: ['./contact.component.css']
})
export class ContactComponent {
  contacts = [
    {
      id: 'linkedin',
      icon: '💼',
      title: 'LinkedIn',
      description: 'Profesyonel bağlantı, iş birliği teklifleri ve kariyer odaklı iletişim için tercih edilen kanalım.',
      buttonText: 'Profili Ziyaret Et',
      url: 'https://www.linkedin.com/in/enesbuyukbas/',
      external: true
    },
    {
      id: 'email',
      icon: '✉️',
      title: 'E-posta',
      description: 'Teknik sorular, ürün geri bildirimleri ve iş birliği önerileri için doğrudan ulaşabilirsiniz.',
      buttonText: 'E-posta Gönder',
      url: 'mailto:enes_bykbss@hotmail.com',
      external: true
    }
  ];

  openLink(url: string, external: boolean): void {
    if (external) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }
}
