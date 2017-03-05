function onRecipeSubmit (event) { 
  var $recipeInput = document.getElementById('recipe-input');
  var $recipeQuery = $recipeInput.value;
  if ($recipeQuery) {
    // enter query into url and fetch recipe
    // return recipe json  
    console.log($recipeQuery)
    $recipeInput.value = ''
  }

  return false;
}   