const SVG_LOADING_ICON = (<div className="loader">
                            <svg className="circular" viewBox="25 25 50 50">
                              <circle className="path" cx="50" cy="50" r="20" fill="none" stroke-width="2" stroke-miterlimit="10"/>
                              </svg>
                            </div>);


var VALID_VEG_OPTIONS = [
  { value: 'NONE', label: 'Non-vegetarian' },
  { value: 'VEG', label: 'Vegetarian' }
];

var VALID_CUISINE_OPTIONS = [
  { value: 'NONE', label: 'No cuisine transformation' },
  { value: 'INDIAN', label: 'Indian' },
  { value: 'GERMAN', label: 'German' },
  { value: 'FRENCH', label: 'French' },
  { value: 'AFRICAN', label: 'African' }
];

var VALID_HEALTH_OPTIONS = [
  { value: 'NONE', label: 'No health transformation' },
  { value: 'HEALTHY', label: 'Healthy' }
]


var RecipeContainer = React.createClass({
  getInitialState: function () {
    return {
      query: '',
      recipe: undefined,
      loading: false,
      vegTransform: 'NONE',
      cuisineTransform: 'NONE',
      healthTransform: 'NONE'
    }
  },

  onChangeRecipe: function (recipe) {
    this.setState({
      query: recipe
    });
  },

  renderRecipe: function (recipe) {
    this.setState({
      recipe: recipe,
      loading: false
    });
  },

  fetchRecipe: function (endpoint, method, recipeUrl, callback) {
    this.setState({
      loading: true
    });
    var url = endpoint; // local
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() { 
      if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
        callback(xmlHttp.responseText);
      }
    }
    xmlHttp.open(method, url, true);
    xmlHttp.send(recipeUrl);
  },

  onTransform: function (value, type) { 
    var changes = {}
    var key;
    switch(type) {
      case 'VEG':
        key = 'vegTransform';
        break;
      case 'CUISINE':
        key = 'cuisineTransform';
        break;
      case 'HEALTH':
        key = 'healthTransform';
        break;
      default:
        return;
    }

    changes[key] = value;
    this.setState(changes);
  },

  render: function () {
    return (
        <div>
          <RecipeForm 
            recipe={this.state.recipe}
            query={this.state.query}
            onChangeRecipe={this.onChangeRecipe}
            fetchRecipe={this.fetchRecipe}
            renderRecipe={this.renderRecipe}
            onTransform={this.onTransform}
            vegTransform={this.state.vegTransform}
            cuisineTransform={this.state.cuisineTransform}
            healthTransform={this.state.healthTransform} />
          <Recipe
            recipe={this.state.recipe}
            loading={this.state.loading} />
        </div>
      );
  }
})

var RecipeForm = React.createClass({

  handleChangeRecipe: function (e) {
    this.props.onChangeRecipe(e.target.value);
  },

  handleSubmit: function (e) {
    var props = this.props;
    e.preventDefault();
    props.fetchRecipe('/fetchRecipe', 'POST', this.props.query, function (response) {
      props.renderRecipe(JSON.parse(response));
    });
  },

  render: function () {
    var props = this.props;
    if (props.recipe == undefined) {
      return (
        <div>
          <h1>Search a recipe and make a transformation</h1>
          <form id="recipe-form" onSubmit={this.handleSubmit}>
            <input id="recipe-input" placeholder="Enter a recipe URL" 
              value={props.query}
              onChange={this.handleChangeRecipe} />
            <div className="recipe-transforms">
              <Select 
                options={VALID_VEG_OPTIONS}
                value={props.vegTransform}
                onChange={ function (value) {
                  props.onTransform(value, 'VEG');
                }} />
              <Select 
                options={VALID_CUISINE_OPTIONS}
                value={props.cuisineTransform}
                onChange={ function (value) {
                  props.onTransform(value, 'CUISINE');
                }} />
              <Select 
                options={VALID_HEALTH_OPTIONS}
                value={props.healthTransform}
                onChange={ function (value) {
                  props.onTransform(value, 'HEALTH');
                }} />
            </div>
            <input id="recipe-search-button" type="submit" value="Submit" />
          </form>
        </div>
      );
    } else {
      return <div></div>;
    }
  }
});

var Recipe = React.createClass({
  renderIngredients: function (list) {
    return list.map(function (item, index) {
      return (
        <div key={index}>
          { item.name }
        </div>
      );
    });
  },

  renderList: function (list) {
    return list.map(function (item, index) {
      return (
        <div key={index}>
          { item }
        </div>
      );
    });
  },

  render: function () {
    if (this.props.recipe != undefined) {
      var recipe = this.props.recipe;
      return (
        <div>
          <div id="recipe">
            <div id="title"><h2>{recipe.title}</h2></div>
            <div className="ingredients"> 
              {this.renderIngredients(recipe.ingredients)}
            </div>
          </div>
        </div>
      );
    } else {

      if (this.props.loading) {
        return (
          <div>{ SVG_LOADING_ICON }</div>
        )
      } else {
        return (
          <div></div>
        );
      }
    }
  }
});

ReactDOM.render(
  React.createElement(RecipeContainer, null),
  document.getElementById('app')
);