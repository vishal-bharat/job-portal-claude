package com.gisma.career.dto;

import lombok.Data;

@Data
public class UpdateProfileRequest {
    private String name;
    private String university;
    private String course;
    private Integer year;
}
