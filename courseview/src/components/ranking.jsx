import React, { Component } from "react";
import Loading from "./loading";
// import axios from "axios";
import { Jumbotron, ListGroup } from "react-bootstrap";

export default class Ranking extends Component {
  state = {
    // course: this.props.course,
    ranklist: null,
    loading: false,
  };

  componentDidMount() {
    this.fetchRanking();
  }

  fetchRanking = () => {
    if (this.props.course) {
      this.setState({
        loading: true,
      });
      this.setState({
        ranklist: [{ name: "diwakar gupta" }],
        loading: false
      });
    }
  };

  // static getDerivedStateFromProps(nextProps, prevState) {
  //     return {
  //         course:nextProps.course
  //     }
  // }

  render() {
    return (
      <Jumbotron>
        {this.state.loading && <Loading />}
        {this.state.ranking ? (
          <ListGroup>
            this.state.ranking.map(view => ( <ListGroup.Item></ListGroup.Item>{" "}
            ))
          </ListGroup>
        ) : (
          "Ranking not available now"
        )}
      </Jumbotron>
    );
  }
}
