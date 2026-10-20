/* Daniela Clemente — Advogada
   JavaScript sem dependências. */
(function () {
  'use strict';

  var reduzido = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- Menu mobile ---- */
  var botaoMenu = document.querySelector('.hamburguer');
  var menu = document.querySelector('.menu-mobile');

  if (botaoMenu && menu) {
    botaoMenu.addEventListener('click', function () {
      var aberto = botaoMenu.getAttribute('aria-expanded') === 'true';
      botaoMenu.setAttribute('aria-expanded', String(!aberto));
      menu.classList.toggle('aberto', !aberto);
      document.body.style.overflow = !aberto ? 'hidden' : '';
    });

    menu.addEventListener('click', function (e) {
      if (e.target.closest('a')) {
        botaoMenu.setAttribute('aria-expanded', 'false');
        menu.classList.remove('aberto');
        document.body.style.overflow = '';
      }
    });

    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape' && menu.classList.contains('aberto')) {
        botaoMenu.setAttribute('aria-expanded', 'false');
        menu.classList.remove('aberto');
        document.body.style.overflow = '';
        botaoMenu.focus();
      }
    });
  }

  /* ---- Borda do cabeçalho ao rolar + botão flutuante ---- */
  var cabecalho = document.querySelector('.cabecalho');
  var flutuante = document.querySelector('.whats-flutuante');

  function aoRolar() {
    var y = window.scrollY;
    if (cabecalho) cabecalho.classList.toggle('rolado', y > 12);
    if (flutuante) flutuante.classList.toggle('visivel', y > 320);
  }
  window.addEventListener('scroll', aoRolar, { passive: true });
  aoRolar();

  /* ---- Revelação progressiva ----
     Exposta em window para que a prévia de arquivo único possa reanimar
     a cada troca de página. */
  var observador = null;

  function revelarTudo() {
    document.querySelectorAll('.revelar').forEach(function (el) {
      el.classList.add('dentro');
    });
  }

  function observarRevelacoes() {
    if (reduzido || !('IntersectionObserver' in window)) {
      revelarTudo();
      return;
    }
    if (!observador) {
      observador = new IntersectionObserver(function (entradas) {
        entradas.forEach(function (entrada) {
          if (entrada.isIntersecting) {
            entrada.target.classList.add('dentro');
            observador.unobserve(entrada.target);
          }
        });
      }, { threshold: 0.1, rootMargin: '0px 0px -6% 0px' });
    }
    document.querySelectorAll('.revelar:not(.dentro)').forEach(function (el) {
      observador.observe(el);
    });
  }

  window.__revelacoes = {
    observar: observarRevelacoes,
    reiniciar: function (raiz) {
      (raiz || document).querySelectorAll('.revelar').forEach(function (el) {
        el.classList.remove('dentro');
        if (observador) observador.unobserve(el);
      });
      observarRevelacoes();
    }
  };

  observarRevelacoes();

  /* ---- Parallax discreto nas fotografias ----
     Deslocamento máximo de poucos pixels: o objetivo é dar profundidade,
     não chamar atenção para o efeito. */
  var camadas = Array.prototype.slice.call(document.querySelectorAll('[data-parallax]'));

  if (camadas.length && !reduzido) {
    var pendente = false;

    function posicionar() {
      var alturaJanela = window.innerHeight;
      camadas.forEach(function (el) {
        var caixa = el.getBoundingClientRect();
        if (caixa.bottom < -200 || caixa.top > alturaJanela + 200) return;
        var fator = parseFloat(el.getAttribute('data-parallax')) || 0.035;
        var centro = caixa.top + caixa.height / 2 - alturaJanela / 2;
        el.style.transform = 'translate3d(0,' + (-centro * fator).toFixed(2) + 'px,0)';
      });
      pendente = false;
    }

    window.addEventListener('scroll', function () {
      if (!pendente) { pendente = true; requestAnimationFrame(posicionar); }
    }, { passive: true });
    window.addEventListener('resize', posicionar, { passive: true });
    posicionar();
  }

  /* ---- Perguntas frequentes ---- */
  document.querySelectorAll('.faq__botao').forEach(function (botao) {
    var painel = document.getElementById(botao.getAttribute('aria-controls'));
    if (!painel) return;

    botao.addEventListener('click', function () {
      var aberto = botao.getAttribute('aria-expanded') === 'true';
      botao.setAttribute('aria-expanded', String(!aberto));

      if (aberto) {
        painel.style.height = painel.scrollHeight + 'px';
        requestAnimationFrame(function () { painel.style.height = '0px'; });
      } else {
        painel.style.height = painel.scrollHeight + 'px';
        painel.addEventListener('transitionend', function fim() {
          painel.style.height = 'auto';
          painel.removeEventListener('transitionend', fim);
        });
      }
    });
  });

  /* ---- Faixa de monograma (elemento de assinatura) ---- */
  document.querySelectorAll('.monograma-faixa').forEach(function (faixa) {
    if (faixa.childElementCount) return;
    var altura = faixa.offsetHeight || 800;
    var quantidade = Math.ceil(altura / 62) + 2;
    var html = '';
    for (var i = 0; i < quantidade; i++) html += '<span aria-hidden="true">D</span>';
    faixa.innerHTML = html;
  });

  /* ---- Formulário de contato ---- */
  var form = document.querySelector('.form');
  if (form) {
    var retorno = form.querySelector('.form__retorno');
    var endpoint = form.getAttribute('data-endpoint') || '';

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var dados = new FormData(form);

      function mostrar(classe, texto) {
        retorno.className = 'form__retorno ' + classe;
        retorno.textContent = texto;
      }

      /* Sem endpoint configurado: encaminha a mensagem pelo WhatsApp. */
      if (!endpoint) {
        var numero = form.getAttribute('data-whatsapp') || '';
        var texto =
          'Olá, Daniela. Sou ' + (dados.get('nome') || '') + '.\n' +
          'Assunto: ' + (dados.get('assunto') || '') + '\n' +
          'E-mail: ' + (dados.get('email') || '') + '\n\n' +
          (dados.get('mensagem') || '');
        window.open('https://wa.me/' + numero + '?text=' + encodeURIComponent(texto), '_blank', 'noopener');
        mostrar('ok', 'Sua mensagem foi aberta no WhatsApp. É só enviar.');
        return;
      }

      var botao = form.querySelector('button[type="submit"]');
      var rotuloOriginal = botao.textContent;
      botao.disabled = true;
      botao.textContent = 'Enviando…';

      fetch(endpoint, { method: 'POST', body: dados, headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error('falha');
          form.reset();
          mostrar('ok', 'Mensagem recebida. O retorno costuma acontecer em até um dia útil.');
        })
        .catch(function () {
          mostrar('erro', 'Não foi possível enviar a mensagem. Tente novamente ou fale diretamente pelo WhatsApp.');
        })
        .finally(function () {
          botao.disabled = false;
          botao.textContent = rotuloOriginal;
        });
    });
  }

  /* ---- Filtros dos conteúdos ---- */
  var filtros = document.querySelectorAll('.filtro');
  if (filtros.length) {
    filtros.forEach(function (botao) {
      botao.addEventListener('click', function () {
        filtros.forEach(function (b) { b.setAttribute('aria-pressed', 'false'); });
        botao.setAttribute('aria-pressed', 'true');
        var cat = botao.getAttribute('data-categoria');
        document.querySelectorAll('[data-artigo]').forEach(function (art) {
          var mostra = cat === 'todos' || art.getAttribute('data-artigo') === cat;
          art.hidden = !mostra;
        });
      });
    });
  }
})();
