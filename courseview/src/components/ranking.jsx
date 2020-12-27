import React, { Component } from "react";
import Loading from "./util/loading";
import axios from "axios";
import { Link } from "react-router-dom";
import { Jumbotron, ListGroup, Col, Row } from "react-bootstrap";
import { FaSync } from "react-icons/fa";

export default class Ranking extends Component {
  state = {
    course: this.props.course,
    ranklist: [],
    loading: false,
  };

  componentDidMount() {
    this.fetchRanking();
  }

  fetchRanking = () => {
    if (this.state.course) {
      this.setState({
        loading: true,
      });
      axios
        .get(`/courses/api/course/${this.state.course}/rank/`, {
          params: { size: 10 },
        })
        .then((res) => {
          console.log(res.data);
          this.setState({
            loading: false,
            ranklist: res.data,
          });
        })
        .catch((mes) => {
          this.setState({
            loading: false,
            ranklist: [],
          });
        });
    }
  };

  static getDerivedStateFromProps(nextProps, prevState) {
    if (nextProps.course != prevState.course) {
      return {
        course: nextProps.course,
      };
    }
    return null;
  }

  render() {
    return (
      <Jumbotron>
        <div
          style={{
            position: "absolute",
            zIndex: 1,
          }}
        >
          <FaSync onClick={this.fetchRanking} />
        </div>
        {this.state.loading ? (
          <Loading />
        ) : (
          <ListGroup>
            {this.state.ranklist.map((user) => (
              <ListGroup.Item
                as={Link}
                to={`/user/${user.username}`}
                target="_blank"
              >
                {user.username}{" "}
                <div style={{ float: "right" }}>{user.score}</div>
              </ListGroup.Item>
            ))}
          </ListGroup>
        )}
      </Jumbotron>
    );
  }
}
