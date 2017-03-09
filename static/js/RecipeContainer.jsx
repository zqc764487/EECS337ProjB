const SVG_LOADING_ICON = (<div className="loader">
                            <svg className="circular" viewBox="25 25 50 50">
                              <circle className="path" cx="50" cy="50" r="20" fill="none" stroke-width="2" stroke-miterlimit="10"/>
                              </svg>
                            </div>);

var RecipeContainer = React.createClass({
  getInitialState: function () {
    return {
      query: '',
      recipe: undefined,
      loading: false
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

  fetchRecipe: function (endpoint, method, recipe, callback) {
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
    xmlHttp.send(null);
  },


  render: function () {
    return (
        <div>
          <RecipeForm 
            recipe={this.state.recipe}
            query={this.state.query}
            onChangeRecipe={this.onChangeRecipe}
            fetchRecipe={this.fetchRecipe}
            renderRecipe={this.renderRecipe} />
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
    props.fetchRecipe('/fetchRecipe', 'GET', this.props.recipe, function (response) {
      props.renderRecipe(JSON.parse(response));
    });
  },

  render: function () {
    if (this.props.recipe == undefined) {
      return (
        <form id="recipe-form" onSubmit={this.handleSubmit}>
          <input id="recipe-input" placeholder="Enter a recipe URL" 
            value={this.props.query}
            onChange={this.handleChangeRecipe} />
          <input id="recipe-search-button" type="submit" value="Submit" />
        </form>
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
      console.log(recipe);
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