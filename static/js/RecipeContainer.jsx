const SVG_LOADING_ICON = (<div className="loader">
                            <svg className="circular" viewBox="25 25 50 50">
                              <circle className="path" cx="50" cy="50" r="20" fill="none" stroke-width="2" stroke-miterlimit="10"/>
                              </svg>
                            </div>);


var VALID_VEG_OPTIONS = [
  { value: 'NONE', label: 'Non-vegetarian' },
  { value: 'veg', label: 'Vegetarian' }
];

var VALID_CUISINE_OPTIONS = [
  { value: 'NONE', label: 'No cuisine transformation' },
  { value: 'indian', label: 'Indian' },
  { value: 'german', label: 'German' },
  { value: 'french', label: 'French' },
  { value: 'african', label: 'African' }
];

var VALID_HEALTH_OPTIONS = [
  { value: 'NONE', label: 'No health transformation' },
  { value: 'healthy', label: 'Healthy' },
  { value: 'lowfat', label: 'Low Fat' },
  { value: 'lowcal', label: 'Low Calorie' },
];

// TEST :http://allrecipes.com/recipe/219929/heathers-fried-chicken/

var RecipeContainer = React.createClass({
  getInitialState: function () {
    return {
      query: '',
      recipe: undefined,
      prev: undefined,
      loading: false,
      vegTransform: VALID_VEG_OPTIONS[0],
      cuisineTransform: VALID_CUISINE_OPTIONS[0],
      healthTransform: VALID_HEALTH_OPTIONS[0]
    }
  },

  onChangeRecipe: function (recipe) {
    this.setState({
      query: recipe
    });
  },

  renderRecipe: function (recipe, prevRecipe) {
    this.setState({
      recipe: recipe,
      prev: prevRecipe,
      loading: false
    });
  },

  fetchRecipe: function (endpoint, method, recipeUrl, callback) {
    if (recipeUrl) {
      this.setState({
        loading: true
      });

      var req = {};
      var url = endpoint; // local
      var xmlHttp = new XMLHttpRequest();

      if (this.state.vegTransform && this.state.vegTransform.value != 'NONE') {
        req['veg'] = true;
      }

      if (this.state.cuisineTransform && this.state.cuisineTransform.value != 'NONE') {
        req['cuisine'] = this.state.cuisineTransform.value;
      }

      if (this.state.healthTransform && this.state.healthTransform.value != 'NONE') {
        req['health'] = this.state.healthTransform.value;
      }

      req['url'] = recipeUrl;

      xmlHttp.onreadystatechange = function() { 
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200) {
          callback(xmlHttp.responseText);
        }
      }
      xmlHttp.open(method, url, true);
      xmlHttp.setRequestHeader('Content-Type', 'application/json');
      xmlHttp.send(JSON.stringify(req));
    }
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
            type="input"
            recipe={this.state.prev}
            loading={this.state.loading} />
          <Recipe
            type="output"
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
      var resp = JSON.parse(response);
      props.renderRecipe(resp.new, resp.old);
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
            <input id="recipe-search-button" className={ this.props.query ? "active" : "inactive" } type="submit" value="Submit" />
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

  renderNumericalList: function (list) {
    return list.map(function (item, index) {
      if (item) {
        return (
          <div key={index}>
            {index + 1}) { item }
          </div>
        );
      }
    });
  },

  render: function () {
    if (this.props.recipe != undefined) {
      var recipe = this.props.recipe;
      return (
        <div>
          <div id="recipe">
            <div id="title"><h2><b className={this.props.type}>{this.props.type.toUpperCase()}:</b> {recipe.title}</h2></div>
            <div className="recipe-content">
              <div className="row clearfix">
                <div className="ingredients"> 
                  <h3>Ingredients</h3>
                  {this.renderIngredients(recipe.ingredients)}
                </div>
                <div className="cooking-tools">
                  <h3>Cooking Tools</h3>
                  {this.renderList(recipe['cooking tools'])}
                </div>
              </div>
              <div className="steps">
                <h3>Steps</h3>
                {this.renderNumericalList(recipe.steps)}
              </div>
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