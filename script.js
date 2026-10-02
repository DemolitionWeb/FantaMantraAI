const profiles = {
  coach: {
    title: 'Head Coach',
    description: 'Coordina i pareri dello Staff e restituisce una scelta chiara: comprare, rilanciare entro il tetto oppure passare.',
    limit: 'Non supera l\'offerta massima calcolata.'
  },
  'sport-director': {
    title: 'Direttore Sportivo',
    description: 'Confronta il prezzo corrente con il budget e con la composizione della rosa già costruita.',
    limit: 'Non presume obiettivi che non hai impostato.'
  },
  budget: {
    title: 'Responsabile Budget',
    description: 'Tiene sotto controllo crediti spesi, crediti rimasti e offerta massima teorica.',
    limit: 'I numeri deterministici dell’app restano il riferimento.'
  },
  mantra: {
    title: 'Analista Mantra',
    description: 'Legge i ruoli indicati e segnala le coperture della rosa senza inventare necessità non definite.',
    limit: 'Non dichiara una carenza senza un obiettivo di rosa.'
  },
  scout: {
    title: 'Scout',
    description: 'Valuta il giocatore solo attraverso le informazioni effettivamente disponibili e verificabili.',
    limit: 'Non attribuisce forma o rendimento senza dati collegati.'
  }
};

const dialog = document.querySelector('#profile-dialog');
const closeDialog = document.querySelector('#dialog-close');

document.querySelectorAll('.profile-button').forEach((button) => {
  button.addEventListener('click', () => {
    const profile = profiles[button.dataset.profile];
    if (!profile) return;

    document.querySelector('#dialog-title').textContent = profile.title;
    document.querySelector('#dialog-description').textContent = profile.description;
    document.querySelector('#dialog-limit').textContent = profile.limit;
    dialog.showModal();
  });
});

closeDialog.addEventListener('click', () => dialog.close());
dialog.addEventListener('click', (event) => {
  if (event.target === dialog) dialog.close();
});

document.querySelector('#theme-toggle').addEventListener('click', () => {
  document.body.classList.toggle('light-theme');
});
