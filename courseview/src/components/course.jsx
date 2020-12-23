import React, { Component } from "react";
import axios from "axios";
import { NavLink, Link } from "react-router-dom";
import {
  Jumbotron,
  Accordion,
  ListGroup,
  Card,
  Breadcrumb,
  Row,
  Col,
} from "react-bootstrap";
import Loading from "./loading";
import Ranking from './ranking';

export default class Course extends Component {
  state = {
    loading: true,
    error: "",
    course: {
      key: this.props.match.params["coursekey"],
      topics: [],
    },
  };

  componentDidMount() {
    axios
      .get(`/courses/api/course/${this.state.course.key}/`)
      .then((res) => {
        this.setState({
          loading: false,
          course: res.data,
        });
      })
      .catch((err) => {
        console.log("error");
        // console.log(err.response);
        console.log(err);

        if (err.response) {
          if (err.response.status === 404) {
            this.setState({ loading: false, error: "Resourse not available" });
          } else {
            this.setState({ loading: false, error: err.response.data });
          }
        } else {
          this.setState({ loading: false, error: err.message });
        }
      });
  }

  renderTopic = (topic, ind) => {
    ind++;
    return (
      <Card key={topic.key}>
        <Accordion.Toggle as={Card.Header} eventKey={ind}>
          {topic.name}
        </Accordion.Toggle>
        <Accordion.Collapse eventKey={ind}>
          <Card.Body>
            <ListGroup variant="flush">
              {topic.subtopics.length === 0 ? (
                <div>No sub Topic Available for now</div>
              ) : (
                topic.subtopics.map((subtopic) => (
                  <ListGroup.Item
                    key={subtopic.key}
                    to={`/courses/s/${this.state.course.key}/${topic.key}/${subtopic.key}`}
                    as={Link}
                  >
                    {subtopic.name}
                  </ListGroup.Item>
                ))
              )}
            </ListGroup>
          </Card.Body>
        </Accordion.Collapse>
      </Card>
    );
  };

  render() {
    const { course } = this.state;
    return (
      <div>
        <Breadcrumb>
          <Breadcrumb.Item linkAs={NavLink} linkProps={{ to: "/courses/s/" }}>
            Courses
          </Breadcrumb.Item>
          <Breadcrumb.Item
            linkAs={NavLink}
            linkProps={{ to: `/courses/s/${this.state.course.key}` }}
          >
            {this.state.course.key}
          </Breadcrumb.Item>
        </Breadcrumb>
        {this.state.loading ? (
          <div className="text-center">
            <Loading />
          </div>
        ) : (
          <div>
            {this.state.error ? (
              <div>{this.state.error}</div>
            ) : (
              <Row>
                <Col md={8}>
                  <Jumbotron>
                    <h3 className="text-center">{course.name}</h3>
                    <p style={{ fontSize: "larger" }}>
                      {this.state.course.description}
                    </p>
                    <Accordion defaultActiveKey="0">
                      {this.state.course.topics.length === 0 ? (
                        <div key={"no topic"}>No Topics Available for now</div>
                      ) : (
                        this.state.course.topics.map((topic, ind) =>
                          this.renderTopic(topic, ind)
                        )
                      )}
                    </Accordion>
                  </Jumbotron>
                </Col>
                <Col>
                  <Ranking course={this.state.course.key}/>
                </Col>
              </Row>
            )}
          </div>
        )}
      </div>
    );
  }
}
