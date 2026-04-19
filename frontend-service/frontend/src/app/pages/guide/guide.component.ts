import { Component, OnInit, AfterViewInit } from '@angular/core';
import { CommonModule } from '@angular/common';

@Component({
  selector: 'app-guide',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './guide.component.html',
  styleUrls: ['./guide.component.css']
})
export class GuideComponent implements OnInit, AfterViewInit {

  // Steps data
  steps = [
    {
      icon: '🔍',
      title: 'Zaman Dilimi Seç',
      desc: '15 dakika, 1 saat, 4 saat veya günlük zaman dilimlerinden stratejine uygun olanı seç.',
      tip: 'Kısa vadeli işlemler için 15m, uzun vade için 4h veya 1d tercih et.'
    },
    {
      icon: '🎯',
      title: 'Güç Filtresi Uygula',
      desc: 'Minimum Strength filtresiyle sadece güçlü sinyalleri listele. 80+ değeri yüksek güvenilirlik gösterir.',
      tip: 'Başlangıç için 70+ filtresini öneririz.'
    },
    {
      icon: '📊',
      title: 'Sinyali Analiz Et',
      desc: 'Coin adına tıklayarak Reasons etiketlerini incele. Trend, Momentum, RSI ve MACD göstergelerini değerlendir.',
      tip: 'Çok sayıda yeşil etiket varsa sinyal daha güvenilirdir.'
    },
    {
      icon: '⚡',
      title: 'İşlem Planla',
      desc: 'Giriş fiyatı, hedef fiyat ve stop loss değerlerini not al. Risk yönetimini asla ihmal etme.',
      tip: 'Stop loss\'u her zaman kullan, tek bir işlemde çok büyük risk alma.'
    }
  ];

  // Indicators data
  indicators: Array<{
    icon: string; name: string; active: boolean;
    short: string; detail: string; example: string;
  }> = [
    {
      icon: '💪', name: 'Strength (Güç)', active: false,
      short: 'Sinyalin güvenilirlik puanı (0-100)',
      detail: 'Birden fazla teknik göstergenin birleşik skoru. Ne kadar yüksekse sinyal o kadar güçlüdür.',
      example: '85 puan → Güçlü sinyal, 60 puan → Orta seviye'
    },
    {
      icon: '⏱️', name: 'Timeframe (Zaman)', active: false,
      short: 'Sinyalin üretildiği mum zaman dilimi',
      detail: '15m = 15 dakikalık mumlar. Daha büyük zaman dilimi, daha uzun vadeli ve genellikle daha güvenilir sinyal anlamına gelir.',
      example: '4h sinyal = Birkaç günlük trend'
    },
    {
      icon: '🎯', name: 'Target (Hedef)', active: false,
      short: 'Fiyatın ulaşması beklenen seviye',
      detail: 'ATR (Average True Range) bazlı hesaplanır. LONG\'da giriş fiyatının üstünde, SHORT\'da altındadır.',
      example: 'Giriş $1.00 → Hedef $1.10 (+%10)'
    },
    {
      icon: '🛡️', name: 'Stop Loss', active: false,
      short: 'Zararı sınırlamak için çıkış noktası',
      detail: 'Bu seviyeye ulaşılırsa işlemden çıkılmalıdır. Risk yönetiminin temelidir.',
      example: 'Giriş $1.00 → Stop $0.95 (-%5 zarar limiti)'
    },
    {
      icon: '📅', name: 'Opened At', active: false,
      short: 'Sinyalin üretildiği tarih ve saat',
      detail: 'Sinyalin ne zaman oluştuğunu gösterir. Eski sinyaller için piyasa koşulları değişmiş olabilir.',
      example: '4h ago → 4 saat önce oluştu'
    },
    {
      icon: '🏷️', name: 'Reasons (Nedenler)', active: false,
      short: 'Sinyali tetikleyen göstergeler',
      detail: 'Her etiket bir teknik analiz göstergesini temsil eder. Ne kadar çok ve çeşitli etiket varsa sinyal o kadar sağlamdır.',
      example: 'Perfect Trend + Strong Momentum + Optimal RSI = Çok güçlü sinyal'
    },
  ];

  // Reason groups data
  reasonGroups = [
    {
      category: 'Trend Göstergeleri',
      color: '#00d395',
      tags: [
        { label: 'Perfect Trend', desc: 'Fiyat güçlü bir yönde ilerliyor' },
        { label: 'Uptrend', desc: 'Fiyat yukarı yönde trend içinde' },
        { label: 'Downtrend', desc: 'Fiyat aşağı yönde trend içinde' },
        { label: 'Strong Trend', desc: 'Trend ivmesi güçlü seyrediyor' },
        { label: 'Weak Trend', desc: 'Trend zayıf, yön belirsiz' },
      ]
    },
    {
      category: 'Momentum Göstergeleri',
      color: '#a78bfa',
      tags: [
        { label: 'Strong Momentum', desc: 'Hareket ivmesi yüksek' },
        { label: 'Good Momentum', desc: 'Hareket ivmesi orta-iyi' },
        { label: 'Weak Momentum', desc: 'Hareket ivmesi düşük' },
        { label: 'Bullish Momentum', desc: 'Yukarı yönlü momentum baskısı' },
        { label: 'Bearish Momentum', desc: 'Aşağı yönlü momentum baskısı' },
      ]
    },
    {
      category: 'ADX Göstergeleri',
      color: '#fb923c',
      tags: [
        { label: 'Very Strong', desc: 'ADX > 40, çok güçlü trend' },
        { label: 'Strong Signal', desc: 'ADX > 25, trend belirgin' },
        { label: 'Moderate Signal', desc: 'ADX 20-25 arası' },
        { label: 'Weak Signal', desc: 'ADX < 20, trend zayıf' },
      ]
    },
    {
      category: 'RSI Göstergeleri',
      color: '#fbbf24',
      tags: [
        { label: 'Optimal RSI', desc: 'RSI optimal alım/satım bölgesinde' },
        { label: 'Healthy RSI', desc: 'RSI dengeli seyirde' },
        { label: 'Oversold', desc: 'RSI < 30, potansiyel yükseliş fırsatı' },
        { label: 'Overbought', desc: 'RSI > 70, potansiyel düşüş riski' },
        { label: 'Neutral RSI', desc: 'RSI nötr bölgede, yön belirsiz' },
      ]
    },
    {
      category: 'MACD Göstergeleri',
      color: '#38bdf8',
      tags: [
        { label: 'Bullish MACD', desc: 'MACD pozitif momentumda' },
        { label: 'Bearish MACD', desc: 'MACD negatif momentumda' },
        { label: 'MACD Crossover Up', desc: 'Yükseliş sinyal kesişimi oluştu' },
        { label: 'MACD Crossover Down', desc: 'Düşüş sinyal kesişimi oluştu' },
      ]
    },
    {
      category: 'Hacim Göstergeleri',
      color: '#f472b6',
      tags: [
        { label: 'High Volume', desc: 'İşlem hacmi ortalamanın üzerinde' },
        { label: 'Low Volume', desc: 'İşlem hacmi ortalamanın altında' },
        { label: 'Volume Spike', desc: 'Anormal hacim artışı var' },
      ]
    },
  ];

  // FAQ data
  faqs: Array<{ open: boolean; q: string; a: string }> = [
    {
      open: false,
      q: 'Sinyaller ne sıklıkla güncelleniyor?',
      a: 'Sinyaller piyasa koşullarına göre sürekli üretilmektedir. 15 dakikalık zaman diliminde her 15 dakikada bir yeni sinyaller oluşabilir.'
    },
    {
      open: false,
      q: 'İşlem açmak için strength değeri kaç olmalı?',
      a: 'Genel öneri 70 ve üzeri. Daha düşük riskli işlemler için 80+ filtresi kullanmanızı tavsiye ederiz.'
    },
    {
      open: false,
      q: 'LONG ve SHORT sinyallerinin farkı nedir?',
      a: 'LONG sinyali fiyatın yükseleceği anlamına gelir. SHORT sinyali ise fiyatın düşeceğini gösterir. Spot işlemlerde genellikle sadece LONG sinyaller kullanılır.'
    },
    {
      open: false,
      q: 'Hangi zaman dilimi daha güvenilir?',
      a: 'Büyük zaman dilimleri (4h, 1d) genellikle daha güvenilirdir ancak daha az sinyal üretir. Küçük zaman dilimleri (15m) daha fazla ama daha riskli sinyal üretir.'
    },
    {
      open: false,
      q: 'Reasons (Nedenler) etiketleri ne işe yarar?',
      a: 'Her etiket bir teknik analiz göstergesini temsil eder. Ne kadar çok ve farklı kategoriden etiket varsa, sinyal o kadar güçlüdür.'
    },
    {
      open: false,
      q: 'Bu sinyaller yatırım tavsiyesi midir?',
      a: 'Hayır. Platformumuz teknik analiz verileri sunar, yatırım tavsiyesi vermez. Tüm kararlar kullanıcıya aittir. Kripto para piyasaları yüksek risk içerir.'
    },
  ];

  ngOnInit(): void {}

  ngAfterViewInit(): void {
    this.animateCounters();
  }

  animateCounters(): void {
    const elements = document.querySelectorAll('.stat-number');
    elements.forEach((el) => {
      const target = parseInt(el.getAttribute('data-target') || '0', 10);
      let current = 0;
      const step = target / 60;
      const timer = setInterval(() => {
        current += step;
        if (current >= target) {
          current = target;
          clearInterval(timer);
        }
        el.textContent = Math.floor(current).toString();
      }, 16);
    });
  }

  toggleFlip(event: Event): void {
    const card = (event.currentTarget as HTMLElement).closest('.flip-card');
    if (card) {
      card.classList.toggle('flipped');
    }
  }
}
