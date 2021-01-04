import React, { Component } from "react";
import Loading from "./util/loading";
import axios from "axios";
import { Link } from "react-router-dom";
import { Jumbotron, ListGroup } from "react-bootstrap";
import { FaSync, FaFileExport } from "react-icons/fa";

export default class Ranking extends Component {
  state = {
    course: this.props.course || this.props?.match?.params?.["coursekey"],
    ranklist: [],
    loading: false,
    size: "10",
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
          params: { size: this.state.size },
        })
        .then((res) => {
          // console.log(res.data);
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

  setSize = (event) => {
    const value = event.target.value;
    this.setState({
      size: value,
    });
  };

  static getDerivedStateFromProps(nextProps, prevState) {
    if (
      nextProps?.match?.params?.["coursekey"] &&
      nextProps?.match?.params?.["coursekey"] !== prevState.course
    ) {
      return {
        course: nextProps.course,
      };
    }
    if (nextProps.course && nextProps.course !== prevState.course) {
      return {
        course: nextProps.course,
      };
    }
    return null;
  }

  render() {
    return (
      <Jumbotron>
        <p>Top Scores</p>
        {this.state.loading ? (
          <Loading />
        ) : (
          <ListGroup>
            {this.state.ranklist&&this.state.ranklist.length?this.state.ranklist.map((user) => (
              <ListGroup.Item
                key={user.username}
                as={Link}
                to={`/user/${user.username}`}
                target="_blank"
              >
                {user.username}{" "}
                <div style={{ float: "right" }}>{user.score}</div>
              </ListGroup.Item>
            )):( <div>No users</div> )}
            
            <div>
              {this.props.course ? (
                <Link to={`/courses/s/${this.state.course}/ranking`}>
                <FaFileExport size={30}/>
                </Link>
                
              ) : (
                <select onChange={this.setSize}>
                  <option value="10">10</option>
                  <option value="20">20</option>
                  <option value="50">50</option>
                  <option value="100">100</option>
                  <option value="all">all</option>
                </select>
              )}
              <FaSync size={30} onClick={this.fetchRanking} />
            </div>
          </ListGroup>
        )}
      </Jumbotron>
    );
  }
}
