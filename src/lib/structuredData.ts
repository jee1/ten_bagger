import type { Lang } from './i18n';

const SITE = 'https://tenbagger.finnaut.com';

export function homeJsonLd(): Record<string, unknown>[] {
  return [
    {
      '@context': 'https://schema.org',
      '@type': 'WebSite',
      '@id': `${SITE}/#website`,
      name: '텐베거 데일리',
      alternateName: ['Ten Bagger Daily', 'Tenbagger Daily', 'Finnaut Tenbagger'],
      url: `${SITE}/`,
      inLanguage: ['ko-KR', 'en-US'],
      description:
        '한국·미국 시장에서 규칙과 데이터로 하루 하나의 텐베거 후보를 기록합니다. 투자 권유가 아니며 수익을 보장하지 않습니다.',
      publisher: { '@id': `${SITE}/#organization` },
    },
    {
      '@context': 'https://schema.org',
      '@type': 'Organization',
      '@id': `${SITE}/#organization`,
      name: 'Finnaut',
      url: `${SITE}/`,
      logo: `${SITE}/og-default.png`,
      sameAs: ['https://blog.funhnc.com/category/FINNAUT'],
      description:
        '규칙 기반 일일 종목 스크리닝 기록(텐베거 데일리)을 운영합니다. 투자 자문사가 아닙니다.',
    },
    {
      '@context': 'https://schema.org',
      '@type': 'SoftwareApplication',
      '@id': `${SITE}/#app`,
      name: '텐베거 데일리',
      applicationCategory: 'FinanceApplication',
      operatingSystem: 'Web',
      url: `${SITE}/`,
      offers: {
        '@type': 'Offer',
        price: '0',
        priceCurrency: 'KRW',
      },
      description:
        '회원가입 없이 이용 가능한 규칙 기반 일일 1픽 스크리닝. 연구·참고용이며 투자 권유가 아닙니다.',
      publisher: { '@id': `${SITE}/#organization` },
      isAccessibleForFree: true,
    },
  ];
}

type FaqItem = { question: string; answer: string };

const aboutFaqKo: FaqItem[] = [
  {
    question: '텐베거 데일리는 무엇인가요?',
    answer:
      '한국·미국 상장 주식을 규칙(Score v2)으로 스크리닝해 하루 하나의 후보만 공개하는 무료 사이트입니다. 선정 이유·축 점수·리스크를 함께 남기며, 회원가입이 없습니다.',
  },
  {
    question: '투자 추천·자문인가요?',
    answer:
      '아닙니다. 투자 권유·자문이 아니며 수익을 보장하지 않습니다. 모든 결정과 손실은 이용자 본인 책임입니다.',
  },
  {
    question: '왜 하루 한 종목인가요?',
    answer:
      '후보를 늘리면 검증·추적이 어려워집니다. 임계 점수(70.0)를 넘는 최고점 1종목만 공개하고, 없으면 없다고 기록합니다. Top-5는 투명성용 관찰 목록이며 추가 공개가 아닙니다.',
  },
  {
    question: 'AI가 종목을 고르나요?',
    answer:
      '선정 본선은 규칙·데이터 점수입니다. (선택적) 관찰용 라벨만 요약 텍스트가 있을 때 보조 분류에 쓰일 수 있으며, 점수·순위를 바꾸지 않습니다. AI가 사라고 한 종목 서비스가 아닙니다.',
  },
  {
    question: '언제·어느 시장을 보나요?',
    answer:
      '매일 06:00 KST. 홀수일=한국(KOSPI·KOSDAQ), 짝수일=미국(NYSE·NASDAQ). 유니버스는 거래소 상장 종목을 매일 갱신합니다.',
  },
  {
    question: '점수는 어떻게 구성되나요?',
    answer:
      'Score v2 가중치 예: 밸류 25% · 성장 20% · 품질 20% · 규모 15% · 진입 10% · 모멘텀 10%. 상세는 선정 방법 페이지를 보세요.',
  },
  {
    question: '회원가입·비용이 있나요?',
    answer:
      '없습니다. 웹에서 바로 보고, RSS로 구독할 수 있습니다.',
  },
  {
    question: "다른 '텐배거' 사이트와 같나요?",
    answer:
      '다릅니다. 유료 차트팩·리딩방·블로그형 장기 리서치와 목적이 다릅니다. 텐베거 데일리는 일일 공개 스크리닝 기록에 초점을 둡니다. 공식 URL은 https://tenbagger.finnaut.com/ 입니다.',
  },
];

const aboutFaqEn: FaqItem[] = [
  {
    question: 'What is Ten Bagger Daily?',
    answer:
      'A free rule-based screener that publishes one Korea or US candidate per day, with reasons, axis scores, and risks — no signup.',
  },
  {
    question: 'Is this investment advice?',
    answer:
      'No. This is not investment advice or solicitation. No returns are promised. All decisions and losses are your own responsibility.',
  },
  {
    question: 'Why only one stock per day?',
    answer:
      'More candidates make verification harder. Only the top-scoring name above threshold (70.0) is published; otherwise we record none. Top-5 is an observational list for transparency, not extra picks.',
  },
  {
    question: 'Does AI pick the stocks?',
    answer:
      'Selection is rule- and data-driven. Optional observational labels may assist classification when summary text exists; they do not change scores or rank. This is not an “AI told me to buy” service.',
  },
  {
    question: 'When and which markets?',
    answer:
      'Daily at 06:00 KST. Odd days: Korea (KOSPI·KOSDAQ). Even days: US (NYSE·NASDAQ). The universe is refreshed daily from exchange listings.',
  },
  {
    question: 'How is the score built?',
    answer:
      'Score v2 weights example: valuation 25% · growth 20% · quality 20% · size 15% · entry 10% · momentum 10%. See the methodology page for details.',
  },
  {
    question: 'Signup or cost?',
    answer:
      'None. View on the web or subscribe via RSS.',
  },
  {
    question: 'Is this the same as other “tenbagger” sites?',
    answer:
      'No. It differs from paid chart packs, signal rooms, and long-form blog research. Ten Bagger Daily focuses on a daily public screening record. Official URL: https://tenbagger.finnaut.com/',
  },
];

export function aboutFaqJsonLd(lang: Lang): Record<string, unknown> {
  const items = lang === 'en' ? aboutFaqEn : aboutFaqKo;
  const pageUrl = lang === 'en' ? `${SITE}/en/about/` : `${SITE}/about/`;
  return {
    '@context': 'https://schema.org',
    '@type': 'FAQPage',
    '@id': `${pageUrl}#faq`,
    mainEntity: items.map((item) => ({
      '@type': 'Question',
      name: item.question,
      acceptedAnswer: {
        '@type': 'Answer',
        text: item.answer,
      },
    })),
  };
}

export function aboutFaqItems(lang: Lang): FaqItem[] {
  return lang === 'en' ? aboutFaqEn : aboutFaqKo;
}
