window.onload = function() {
// get a new date (locale machine date time)
const date = new Date();
// get the date as a string
const datestring = date.toDateString();
// get the time as a string
const timestring = date.toLocaleTimeString();
// Insert time in html
//document.getElementById('timestring').innerHTML = timestring
// Setup Choice-js for #price_notification_method 
const percentNotificationMethodForm = $('#percent_notification_method')[0];
const percentNotificationMethodChoice = new Choices(percentNotificationMethodForm, {
    renderChoiceLimit: -1,
    maxItemCount: 2,
    removeItems: true,
    removeItemButton: true,
    loadingText: 'Chargement...',
    noResultsText: 'Aucun résultat trouvé',
    noChoicesText: 'Aucun choix possible à partir de',
    itemSelectText: 'Cliquez pour sélectionner',
    addItemText: (value) => {
      return `Appuyez sur entrée pour ajouter <b>"${value}"</b>`;
    },
    maxItemText: (maxItemCount) => {
      return `Vous pouvez choisir ${maxItemCount} options maximum`;
    },
    valueComparer: (value1, value2) => {
      return value1 === value2;
    }
  });
}