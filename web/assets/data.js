const DADOS = {
  usuario: {
    nome: "Miguel F.",
    iniciais: "MF",
  },

  perfil: {
    curso: "Engenharia de Software",
    periodo: 4,
    habilidades: ["Python", "Git", "JavaScript", "React", "SQL", "Java"],
    cidade: "Rio de Janeiro, RJ",
    modalidade: "remoto",
    notaMinima: 60,
  },

  configuracoes: {
    telegramChatId: "123456789",
    horarioEntrega: "08:00",
    quantidadeVagas: 5,
    diasRecentes: 2,
    fontes: [
      { nome: "Adzuna", estado: "ativa" },
      { nome: "Gupy", estado: "em breve" },
      { nome: "Vagas.com", estado: "em breve" },
      { nome: "InfoJobs", estado: "em breve" },
    ],
  },

  hoje: {
    data: "26/08/2026",
    vagas: [
      {
        id: "adz-1001",
        titulo: "Estágio em Desenvolvimento Back-end (Python)",
        empresa: "Nubank",
        localizacao: "Remoto — Brasil",
        modalidade: "remoto",
        publicada: "há 1 dia",
        nota: 92,
        motivo:
          "Pede Python, SQL e Git — três das suas habilidades — e aceita 4º período. Time descrito como de produto, alinhado ao seu curso.",
        alerta: null,
        estado: "enviada",
      },
      {
        id: "adz-1002",
        titulo: "Estágio Front-end React",
        empresa: "iFood",
        localizacao: "São Paulo, SP (híbrido)",
        modalidade: "hibrido",
        publicada: "há 2 dias",
        nota: 78,
        motivo:
          "Forte match de stack (React, JavaScript, Git). Perde pontos porque é híbrido em SP e você marcou preferência por remoto.",
        alerta: "Vaga é híbrida em São Paulo; exige presença 2x/semana.",
        estado: "enviada",
      },
      {
        id: "adz-1003",
        titulo: "Estágio em Engenharia de Dados",
        empresa: "Loft",
        localizacao: "Remoto — Brasil",
        modalidade: "remoto",
        publicada: "há 1 dia",
        nota: 71,
        motivo:
          "SQL e Python cobrem o núcleo da vaga. Falta experiência com pipelines/ETL citada como diferencial, mas não é obrigatória.",
        alerta: null,
        estado: "enviada",
      },
      {
        id: "adz-1004",
        titulo: "Estágio em QA / Automação de Testes",
        empresa: "Stone",
        localizacao: "Rio de Janeiro, RJ (presencial)",
        modalidade: "presencial",
        publicada: "há 2 dias",
        nota: 54,
        motivo:
          "É na sua cidade e usa Java, que você tem. Presencial e foco em QA, área que não aparece no seu perfil como interesse principal.",
        alerta: "Presencial no Porto Maravilha; carga de 30h semanais.",
        estado: "enviada",
      },
      {
        id: "adz-1005",
        titulo: "Jovem Aprendiz — Suporte de TI",
        empresa: "Consultoria Alfa",
        localizacao: "Remoto",
        modalidade: "remoto",
        publicada: "há 3 dias",
        nota: 28,
        motivo:
          "Programa de aprendiz, não estágio de graduação. Atividades de suporte e helpdesk, sem desenvolvimento de software.",
        alerta: "É contrato de Jovem Aprendiz, não estágio; exige ensino médio, não superior.",
        estado: "descartada",
      },
    ],
  },

  historico: [
    { data: "25/08/2026", titulo: "Estágio Python Júnior", empresa: "PicPay", nota: 84, estado: "curtida", url: "#" },
    { data: "25/08/2026", titulo: "Estágio Desenvolvedor Full-stack", empresa: "Movile", nota: 76, estado: "enviada", url: "#" },
    { data: "24/08/2026", titulo: "Estágio em Ciência de Dados", empresa: "Serasa", nota: 69, estado: "enviada", url: "#" },
    { data: "24/08/2026", titulo: "Estágio Back-end Node", empresa: "QuintoAndar", nota: 58, estado: "descartada", url: "#" },
    { data: "23/08/2026", titulo: "Estágio React Native", empresa: "Mercado Livre", nota: 81, estado: "curtida", url: "#" },
    { data: "23/08/2026", titulo: "Estágio em Infraestrutura / DevOps", empresa: "Locaweb", nota: 47, estado: "descartada", url: "#" },
    { data: "22/08/2026", titulo: "Estágio Desenvolvimento Java", empresa: "TOTVS", nota: 63, estado: "enviada", url: "#" },
    { data: "22/08/2026", titulo: "Estágio Front-end", empresa: "Hotmart", nota: 74, estado: "enviada", url: "#" },
    { data: "21/08/2026", titulo: "Estágio em Análise de Sistemas", empresa: "Banco BV", nota: 52, estado: "descartada", url: "#" },
    { data: "21/08/2026", titulo: "Estágio Python + IA", empresa: "Take Blip", nota: 88, estado: "curtida", url: "#" },
  ],

  mercado: {
    numeros: [
      { valor: "312", rotulo: "Vagas avaliadas em 30 dias" },
      { valor: "41", rotulo: "Compatíveis com o seu perfil" },
      { valor: "68", rotulo: "Nota média das compatíveis" },
      { valor: "73%", rotulo: "Vagas remotas ou híbridas" },
    ],
    habilidades: [
      { nome: "Python", valor: 58 },
      { nome: "React", valor: 44 },
      { nome: "SQL", valor: 39 },
      { nome: "JavaScript", valor: 37 },
      { nome: "Git", valor: 31 },
      { nome: "Java", valor: 22 },
      { nome: "Docker", valor: 18 },
    ],
    modalidades: [
      { nome: "Remoto", valor: 51 },
      { nome: "Híbrido", valor: 22 },
      { nome: "Presencial", valor: 27 },
    ],
    empresas: [
      { nome: "Nubank", valor: 9 },
      { nome: "iFood", valor: 7 },
      { nome: "Mercado Livre", valor: 6 },
      { nome: "Stone", valor: 5 },
      { nome: "PicPay", valor: 4 },
    ],
  },
};
