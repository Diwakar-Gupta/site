import React, { Component } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import { Jumbotron, ListGroup, Row, Col } from "react-bootstrap";
import Loading from "./util/loading";
import Ranking from "./ranking";
import BreadCrumb from "./util/breadcrumb";

export default class CourseSubTopics extends Component {
  state = {
    loading: true,
    error: "",
    coursekey: this.props.match.params["coursekey"],
    topickey: this.props.match.params["topickey"],
    subtopic: {
      key: this.props.match.params["subtopickey"],
    },
  };

  componentDidMount() {
    axios
      .get(
        `/courses/api/course/${this.state.coursekey}/${this.state.topickey}/${this.state.subtopic.key}`
      )
      .then((res) => {
        console.log(res.data);
        this.setState({
          loading: false,
          subtopic: res.data,
        });
      })
      .catch((mes) => {
        this.setState({
          loading: false,
          error: "Some thing went wrong",
        });
      })
      .catch(console.log);
  }

  renderProblem = (problem, ind) => {
    ind++;
    return (
      <ListGroup.Item as={Link} to={`${problem.url}`} target="_blank">
        <Row style={problem.result ? { background: "#c3eefe" } : {}}>
          <Col> {problem.name}</Col>
          {problem.result ? "done  " : ""}
          {problem.points}
        </Row>
      </ListGroup.Item>
    );
  };

  render() {
    const { problems } = this.state.subtopic || [];
    return (
      <div>
        <BreadCrumb
          coursename={this.state.coursekey}
          coursekey={this.state.coursekey}
          subtopicname={this.state.subtopic.name}
          subtopicurl={`/courses/s/${this.state.coursekey}/${this.state.topickey}/${this.state.subtopic.key}`}
        />
        {this.state.loading ? (
          <div className="text-center">
            <Loading />
          </div>
        ) : (
          <div>
            {this.state.error ? (
              <div>Some thing went wrong</div>
            ) : (
              <Row>
                <Col md={8}>
                  <Jumbotron>
                    <h3 className="text-center">{this.state.subtopic.name}</h3>
                    {problems.length === 0 ? (
                      <div>No Question Here</div>
                    ) : (
                      <ListGroup variant="flush">
                        {problems.map(this.renderProblem)}
                      </ListGroup>
                    )}
                  </Jumbotron>
                </Col>
                <Col>
                  <Ranking course={this.state.coursekey} />
                </Col>
              </Row>
            )}
          </div>
        )}
      </div>
    );
  }
}
